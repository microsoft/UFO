from torchvision import transforms
from torchvision.transforms.functional import InterpolationMode
import torch

class BlipImageEvalProcessor:
    def __init__(self, image_size=384, mean=None, std=None):
        super().__init__()
        if mean is None:
            mean = (0.48145466, 0.4578275, 0.40821073)
        if std is None:
            std = (0.26862954, 0.26130258, 0.27577711)

        self.normalize = transforms.Normalize(mean, std)

        self.transform = transforms.Compose(
            [
                transforms.Resize(
                    (image_size, image_size), interpolation=InterpolationMode.BICUBIC
                ),
                transforms.ToTensor(),
                self.normalize,
            ]
        )

    def __call__(self, item):
        return self.transform(item)

from functools import partial

def blip2_image_processor_func_with_inputs(image_processor, image):
    return {'image': image_processor(image).unsqueeze(0), 'input_ids': torch.zeros(1, 1, dtype=torch.long), 'position_ids': None, 'attention_mask': torch.ones(1, 1, dtype=torch.long)}

def get_image_processor(image_size):
    return partial(blip2_image_processor_func_with_inputs, BlipImageEvalProcessor(image_size))