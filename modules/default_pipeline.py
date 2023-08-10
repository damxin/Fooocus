import os
import torch
import modules.core as core

from modules.path import modelfile_path


xl_base_filename = os.path.join(modelfile_path, 'sd_xl_base_1.0.safetensors')
xl_refiner_filename = os.path.join(modelfile_path, 'sd_xl_refiner_1.0.safetensors')

xl_base = core.load_model(xl_base_filename)
xl_refiner = core.load_model(xl_refiner_filename)
del xl_base.vae


@torch.no_grad()
def process(positive_prompt, negative_prompt, width=1024, height=1024, batch_size=1):
    positive_conditions = core.encode_prompt_condition(clip=xl_base.clip, prompt=positive_prompt)
    negative_conditions = core.encode_prompt_condition(clip=xl_base.clip, prompt=negative_prompt)

    positive_conditions_refiner = core.encode_prompt_condition(clip=xl_refiner.clip, prompt=positive_prompt)
    negative_conditions_refiner = core.encode_prompt_condition(clip=xl_refiner.clip, prompt=negative_prompt)

    empty_latent = core.generate_empty_latent(width=width, height=height, batch_size=batch_size)

    sampled_latent = core.ksample(
        unet=xl_base.unet,
        positive_condition=positive_conditions,
        negative_condition=negative_conditions,
        latent_image=empty_latent,
        steps=30, start_at_step=0, end_at_step=20, return_with_leftover_noise=True, add_noise=True
    )

    sampled_latent = core.ksample(
        unet=xl_refiner.unet,
        positive_condition=positive_conditions_refiner,
        negative_condition=negative_conditions_refiner,
        latent_image=sampled_latent,
        steps=30, start_at_step=20, end_at_step=30, return_with_leftover_noise=False, add_noise=False
    )

    decoded_latent = core.decode_vae(vae=xl_refiner.vae, latent_image=sampled_latent)

    images = core.image_to_numpy(decoded_latent)
    return images
