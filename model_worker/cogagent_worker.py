"""
A model worker executes the model.
"""
import argparse
import time
import uuid

from fastapi import FastAPI, Request
import torch
import uvicorn
from functools import partial

from PIL import Image
from io import BytesIO
import base64

from sat.model.mixins import CachedAutoregressiveMixin
from models.cogagent_model import FineTuneTrainCogAgentModel

from utils import build_logger, chat, llama2_tokenizer, llama2_text_processor_inference, get_image_processor


GB = 1 << 30

worker_id = str(uuid.uuid4())[:6]
logger = build_logger("model_worker", f"model_worker_{worker_id}.log")


def load_image_from_base64(image):
    return Image.open(BytesIO(base64.b64decode(image))).convert("RGB")


class ModelWorker:
    def __init__(self, args):

        args.stream_chat = False
        self.args = args
    
        # load model
        model, model_args = FineTuneTrainCogAgentModel.from_pretrained(
            args.from_pretrained,
            args=argparse.Namespace(
                deepspeed=None,
                local_rank=0,
                rank=0,
                world_size=1,
                model_parallel_size=1,
                mode='inference',
                skip_init=True,
                use_gpu_initialization=True if torch.cuda.is_available() else False,
                device='cuda',
                **vars(args)
        ))
        model.add_mixin('auto-regressive', CachedAutoregressiveMixin())
        self.model = model.eval()

        self.tokenizer = llama2_tokenizer(args.local_tokenizer, signal_type=args.version)
        self.image_processor = get_image_processor(224)
        self.cross_image_processor = get_image_processor(1120)
        self.text_processor_infer = llama2_text_processor_inference(self.tokenizer, args.max_length, model.image_length)


    @torch.inference_mode()
    def direct_generate(self, params):

        prompt = params["prompt"]
        history = params.get("history", [])
        image_base64 = params.get("image", None)
        image_mode = params.get("image_mode", "copy") # copy or resize
        image_path = None
        if image_base64 is not None:
            image = load_image_from_base64(image_base64)

        max_size = (1120, 1120)
        if image_mode == "resize":
            scale = min(max_size[0] / image.size[0], max_size[1] / image.size[1])
            image = image.resize((int(image.size[0] * scale), int(image.size[1] * scale)), Image.BILINEAR)

        padded_image = Image.new("RGB", max_size, color="white")
        padded_image.paste(image, (0, 0))
        image = padded_image

        start_time = time.time()
        response, history, cache_image = chat(
            image_path,
            self.model,
            self.text_processor_infer,
            self.image_processor,
            prompt,
            history=history,
            cross_img_processor=self.cross_image_processor,
            image=image,
            max_length=args.max_length,
            top_p=args.top_p,
            temperature=args.temperature,
            top_k=args.top_k,
            invalid_slices=self.text_processor_infer.invalid_slices,
            args=args
        )
        duration = time.time() - start_time
        print("response", response)
        print("duration", duration)

        response = {
            "text": response,
            "duration": duration,
            "history": history,
            "error_code": 0
        }
        return response


app = FastAPI()

@app.post("/chat/completions")
async def generate(request: Request):
    params = await request.json()
    response_data = worker.direct_generate(params)
    return response_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=11434)

    parser.add_argument("--max_length", type=int, default=2048, help='max length of the total sequence')
    parser.add_argument("--top_p", type=float, default=0.4, help='top p for nucleus sampling')
    parser.add_argument("--top_k", type=int, default=1, help='top k for top k sampling')
    parser.add_argument("--temperature", type=float, default=.8, help='temperature for sampling')
    parser.add_argument("--chinese", action='store_true', help='Chinese interface')
    parser.add_argument("--version", type=str, default="chat", choices=['chat', 'vqa', 'chat_old', 'base'], help='version of language process. if there is \"text_processor_version\" in model_config.json, this option will be overwritten')
    parser.add_argument("--quant", choices=[8, 4], type=int, default=None, help='quantization bits')

    parser.add_argument("--stream_chat", action='store_true', help='streaming chat')

    parser.add_argument("--from_pretrained", type=str, default="checkpoints/ScreenAgent-2312", help='pretrained ckpt')
    parser.add_argument("--local_tokenizer", type=str, default="lmsys/vicuna-7b-v1.5", help='tokenizer path')
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--bf16", action="store_true")

    args = parser.parse_args()
    logger.info(f"args: {args}")

    worker = ModelWorker(args)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")