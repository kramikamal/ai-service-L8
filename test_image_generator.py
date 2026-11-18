import base64
from io import BytesIO
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from PIL import Image

from routers.image_generator import ImageRequest, post_image


class ProductImageTests(unittest.TestCase):
    @patch("routers.image_generator.generate")
    def test_base64_image_fits_inside_product(self, generate):
        source = BytesIO()
        Image.effect_noise((1024, 1024), 90).convert("RGB").save(source, "PNG")
        generate.return_value = {"data": [{"b64_json": base64.b64encode(source.getvalue()).decode()}]}

        result = post_image(ImageRequest(name="Toy", description="A rope toy"))
        prefix, encoded = result["image"].split(",", 1)
        self.assertEqual(prefix, "data:image/jpeg;base64")
        self.assertLess(len(result["image"]), 140_000)
        with Image.open(BytesIO(base64.b64decode(encoded))) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertLessEqual(max(image.size), 384)

    @patch("routers.image_generator.generate", return_value={"data": [{}]})
    def test_missing_image_is_a_provider_error(self, _generate):
        with self.assertRaises(HTTPException) as error:
            post_image(ImageRequest(name="Toy", description="A rope toy"))
        self.assertEqual(error.exception.status_code, 502)
