# Method to generate response from prompt and image using the Llava model
@torch.inference_mode()
def direct_generate_llava(self, params):
    tokenizer, model, image_processor = self.tokenizer, self.model, self.image_processor

    prompt = params["prompt"]
    image = params.get("image", None)
    if image is not None:
        if DEFAULT_IMAGE_TOKEN not in prompt:
            raise ValueError(
                "Number of image does not match number of <image> tokens in prompt"
            )

        image = load_image_from_base64(image)
        image = image_processor.preprocess(image, return_tensors="pt")["pixel_values"][
            0
        ]
        image = image.to(self.model.device, dtype=self.model.dtype)
        images = image.unsqueeze(0)

        replace_token = DEFAULT_IMAGE_TOKEN
        if getattr(self.model.config, "mm_use_im_start_end", False):
            replace_token = (
                DEFAULT_IM_START_TOKEN + replace_token + DEFAULT_IM_END_TOKEN
            )
        prompt = prompt.replace(DEFAULT_IMAGE_TOKEN, replace_token)

        num_image_tokens = (
            prompt.count(replace_token) * model.get_vision_tower().num_patches
        )
    else:
        return {"text": "No image provided", "error_code": 0}

    temperature = float(params.get("temperature", 1.0))
    top_p = float(params.get("top_p", 1.0))
    max_context_length = getattr(model.config, "max_position_embeddings", 2048)
    max_new_tokens = min(int(params.get("max_new_tokens", 256)), 1024)
    stop_str = params.get("stop", None)
    do_sample = True if temperature > 0.001 else False
    input_ids = (
        tokenizer_image_token(prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors="pt")
        .unsqueeze(0)
        .to(self.device)
    )
    keywords = [stop_str]
    max_new_tokens = min(
        max_new_tokens, max_context_length - input_ids.shape[-1] - num_image_tokens
    )

    input_ids = (
        tokenizer_image_token(prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors="pt")
        .unsqueeze(0)
        .to(self.device)
    )

    input_seq_len = input_ids.shape[1]

    generation_output = self.model.generate(
        inputs=input_ids,
        do_sample=do_sample,
        temperature=temperature,
        top_p=top_p,
        max_new_tokens=max_new_tokens,
        images=images,
        use_cache=True,
    )

    generation_output = generation_output[0, input_seq_len:]
    decoded = tokenizer.decode(generation_output, skip_special_tokens=True)

    response = {"text": decoded}
    print("response", response)
    return response


# The API is included in llava and cogagent installations. If you customize your model, you can install fastapi via pip or uncomment the library in the requirements.
# import FastAPI
# app = FastAPI()


# For llava
@app.post("/chat/completions")
async def generate_llava(request: Request):
    params = await request.json()
    response_data = worker.direct_generate_llava(params)
    return response_data
