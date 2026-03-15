"""Tests for the generate_image tool."""

import base64
from unittest.mock import MagicMock, patch

import pytest

from postable_ia.tools import ImageGenerationError, generate_image, resolve_image_ref, _IMG_REF_PREFIX
from postable_ia.config import settings


def _make_inline_data(data: bytes, mime_type: str = "image/png") -> MagicMock:
    inline = MagicMock()
    inline.data = data
    inline.mime_type = mime_type
    return inline


def _make_response_with_image(data: bytes, mime_type: str = "image/png") -> MagicMock:
    part = MagicMock()
    part.inline_data = _make_inline_data(data, mime_type)
    response = MagicMock()
    response.parts = [part]
    response.candidates = []
    return response


def _make_response_no_image() -> MagicMock:
    part = MagicMock()
    part.inline_data = None
    response = MagicMock()
    response.parts = [part]
    response.candidates = []
    return response


_VALID_IMAGE_BYTES = b"\x89PNG\r\n" + b"x" * 200


class TestGenerateImageHappyPath:
    def test_returns_correct_keys(self):
        with patch("postable_ia.tools.genai.Client") as mock_client_cls, \
             patch("postable_ia.tools.time.sleep"):
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.models.generate_content.return_value = _make_response_with_image(
                _VALID_IMAGE_BYTES
            )
            result = generate_image("padaria artesanal em Curitiba")
        assert "image_base64" in result
        assert "image_mime_type" in result
        assert "mime_type" not in result

    def test_image_base64_is_ref_token(self):
        with patch("postable_ia.tools.genai.Client") as mock_client_cls, \
             patch("postable_ia.tools.time.sleep"):
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.models.generate_content.return_value = _make_response_with_image(
                _VALID_IMAGE_BYTES
            )
            result = generate_image("café colonial")
        assert result["image_base64"].startswith(_IMG_REF_PREFIX)

    def test_resolve_image_ref_returns_real_base64(self):
        with patch("postable_ia.tools.genai.Client") as mock_client_cls, \
             patch("postable_ia.tools.time.sleep"):
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.models.generate_content.return_value = _make_response_with_image(
                _VALID_IMAGE_BYTES
            )
            result = generate_image("café colonial")
        stored = resolve_image_ref(result["image_base64"])
        assert stored is not None
        decoded = base64.b64decode(stored["image_base64"])
        assert decoded == _VALID_IMAGE_BYTES

    def test_uses_settings_image_model(self):
        with patch("postable_ia.tools.genai.Client") as mock_client_cls, \
             patch("postable_ia.tools.time.sleep"):
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.models.generate_content.return_value = _make_response_with_image(
                _VALID_IMAGE_BYTES
            )
            generate_image("restaurante japonês")
        call_kwargs = mock_client.models.generate_content.call_args
        assert call_kwargs.kwargs["model"] == settings.image_model or \
               call_kwargs[1]["model"] == settings.image_model or \
               call_kwargs[0][0] == settings.image_model

    def test_skips_text_parts_before_image_part(self):
        text_part = MagicMock()
        text_part.inline_data = None
        image_part = MagicMock()
        image_part.inline_data = _make_inline_data(_VALID_IMAGE_BYTES, "image/png")
        response = MagicMock()
        response.parts = [text_part, image_part]
        response.candidates = []

        with patch("postable_ia.tools.genai.Client") as mock_client_cls, \
             patch("postable_ia.tools.time.sleep"):
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.models.generate_content.return_value = response
            result = generate_image("loja de flores")
        assert result["image_base64"].startswith(_IMG_REF_PREFIX)


class TestGenerateImageNoImagePart:
    def test_raises_image_generation_error_after_retries(self):
        with patch("postable_ia.tools.genai.Client") as mock_client_cls, \
             patch("postable_ia.tools.time.sleep"):
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.models.generate_content.return_value = _make_response_no_image()
            with pytest.raises(ImageGenerationError):
                generate_image("sem imagem")

    def test_retries_correct_number_of_times(self):
        with patch("postable_ia.tools.genai.Client") as mock_client_cls, \
             patch("postable_ia.tools.time.sleep"):
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.models.generate_content.return_value = _make_response_no_image()
            with pytest.raises(ImageGenerationError):
                generate_image("sem imagem")
        assert mock_client.models.generate_content.call_count == settings.image_max_retries


class TestGenerateImageAPIException:
    def test_raises_after_all_retries(self):
        with patch("postable_ia.tools.genai.Client") as mock_client_cls, \
             patch("postable_ia.tools.time.sleep"):
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.models.generate_content.side_effect = RuntimeError("API down")
            with pytest.raises(ImageGenerationError):
                generate_image("erro de api")

    def test_sleeps_between_retries(self):
        with patch("postable_ia.tools.genai.Client") as mock_client_cls, \
             patch("postable_ia.tools.time.sleep") as mock_sleep:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.models.generate_content.side_effect = RuntimeError("API down")
            with pytest.raises(ImageGenerationError):
                generate_image("erro de api")
        assert mock_sleep.call_count == settings.image_max_retries - 1

    def test_never_returns_silent_empty_dict(self):
        with patch("postable_ia.tools.genai.Client") as mock_client_cls, \
             patch("postable_ia.tools.time.sleep"):
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.models.generate_content.side_effect = RuntimeError("API down")
            with pytest.raises(ImageGenerationError):
                generate_image("erro silencioso")


class TestGenerateImageRetrySuccess:
    def test_succeeds_on_second_attempt(self):
        responses = [
            _make_response_no_image(),
            _make_response_with_image(_VALID_IMAGE_BYTES),
        ]
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            r = responses[call_count]
            call_count += 1
            return r

        with patch("postable_ia.tools.genai.Client") as mock_client_cls, \
             patch("postable_ia.tools.time.sleep") as mock_sleep:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.models.generate_content.side_effect = side_effect
            result = generate_image("segunda tentativa")
        assert result["image_base64"].startswith(_IMG_REF_PREFIX)
        assert mock_sleep.call_count == 1

    def test_succeeds_on_third_attempt(self):
        responses = [
            _make_response_no_image(),
            _make_response_no_image(),
            _make_response_with_image(_VALID_IMAGE_BYTES),
        ]
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            r = responses[call_count]
            call_count += 1
            return r

        with patch("postable_ia.tools.genai.Client") as mock_client_cls, \
             patch("postable_ia.tools.time.sleep") as mock_sleep:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.models.generate_content.side_effect = side_effect
            result = generate_image("terceira tentativa")
        assert result["image_base64"].startswith(_IMG_REF_PREFIX)
        assert mock_sleep.call_count == 2


class TestGenerateImageRetryExhaustion:
    def test_raises_image_generation_error_not_raw_runtime_error(self):
        with patch("postable_ia.tools.genai.Client") as mock_client_cls, \
             patch("postable_ia.tools.time.sleep"):
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.models.generate_content.side_effect = RuntimeError("boom")
            exc = None
            try:
                generate_image("exaustão")
            except Exception as e:
                exc = e
        assert isinstance(exc, ImageGenerationError)

    def test_image_generation_error_is_runtime_error_subclass(self):
        assert issubclass(ImageGenerationError, RuntimeError)


class TestGenerateImageReturnKeys:
    def test_image_mime_type_in_result(self):
        with patch("postable_ia.tools.genai.Client") as mock_client_cls, \
             patch("postable_ia.tools.time.sleep"):
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.models.generate_content.return_value = _make_response_with_image(
                _VALID_IMAGE_BYTES, "image/png"
            )
            result = generate_image("chave correta")
        assert "image_mime_type" in result
        assert "mime_type" not in result
