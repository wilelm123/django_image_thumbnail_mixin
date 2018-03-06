import os
import io
import hashlib
import logging

from PIL import Image
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile


logger = logging.getLogger(__name__)


class ImageThumbnailMixin:
    """
    Before to use, you should set IMAGE_FIELD, THUMBNAIL_FIELD, BASE_SIZE first,

    for example:

    class User(models.Model, ImageThumbnailMixin):
        name = models.CharField(max_length=100)
        avatar = models.ImageField(upload_to=settings.UPLOAD_TO, null=True, blank=True)
        thumbnail = models.Image(upload_to=settings.UPLOAD_TO, null=True, blank=True)

        IMAGE_FIELD, THUMBNAIL_FIELD, BASE_SIZE = "avatar", "thumbnail", 100

        def save(self, *args, **kwargs):
            res = super().save(*args, **kwargs)
            self.create_thumbnail()     # should put after super calling
            return res

    """

    IMAGE_FIELD, THUMBNAIL_FIELD, THUMBNAIL_BASE_SIZE = None, None, 200

    def __init__(self, *args, **kwargs):
        assert self.IMAGE_FIELD is not None, "ImageThumbnailMixin should set IMAGE_FIELD first"
        assert self.THUMBNAIL_FIELD is not None, "ImageThumbnailMixin should set THUMBNAIL_FIELD first"
        self.key_prefix = "IMAGE_CACHE_{0}".format(self.__class__.__name__)
        super(ImageThumbnailMixin, self).__init__(*args, **kwargs)

    def cache_old_image_md5(self):
        image_md5 = self.get_image_md5()
        key = "{0}_{1}".format(self.key_prefix, self.id)
        cache.set(key, image_md5)

    def get_image_md5(self):
        image = getattr(self, self.IMAGE_FIELD)
        if not image or not image._file:
            return None
        md5 = hashlib.md5()
        for chunk in image.chunks():
            md5.update(chunk)
        val = md5.hexdigest()
        image.seek(0)
        logger.debug("Image md5 val: %s", val)
        return val

    def image_changed(self):
        key = "{0}_{1}".format(self.key_prefix, self.id)
        cached_md5 = cache.get(key)
        new_md5 = self.get_image_md5()
        logger.debug("Cached Image Md5: %s", cached_md5)
        logger.debug("New Image Md5: %s", new_md5)
        if cached_md5 != new_md5:
            self.cache_old_image_md5()
        return cached_md5 != new_md5

    def get_image_format(self):
        try:
            image = getattr(self, self.IMAGE_FIELD)
            f = io.BytesIO(image.read())
            img = Image.open(f)
            image.seek(0)
            return img.format
        except OSError as exc:
            logger.error("Get image file format error: %s", exc)
            return None

    def create_thumbnail(self):
        """
        Create model image field thumbnail
        """

        image_field = getattr(self, self.IMAGE_FIELD)
        thumbnail_field = getattr(self, self.THUMBNAIL_FIELD)

        logger.debug("===== Now check the image validation: %s", image_field.name)
        img_format = self.get_image_format()
        # image field not set or file is not image or image not changed
        if not image_field or not img_format or not self.image_changed():
            logger.error("===== Skip create thumbnail")
            return
        logger.debug("Done")

        logger.debug("====== Now Create thumbnail for the given image: %s", image_field.name)

        django_type = "image/{0}".format(img_format.lower())
        pil_type, file_extension = "jpeg", 'jpg'

        if django_type == "image/png":
            pil_type, file_extension = 'png', 'png'
        img = Image.open(io.BytesIO(image_field.read()))
        w_percent = self.THUMBNAIL_BASE_SIZE / float(img.size[0])
        h_size = int(float(img.size[1]) * w_percent)
        img.thumbnail([self.THUMBNAIL_BASE_SIZE, h_size], Image.ANTIALIAS)

        temp_handler = io.BytesIO()
        img.save(temp_handler, pil_type)
        temp_handler.seek(0)
        base_name = os.path.splitext(os.path.split(image_field.name)[-1])[0]
        file_name = '{0}_thumbnail.{1}'.format(base_name, file_extension)
        suf = SimpleUploadedFile(file_name, temp_handler.read(),
                                 content_type=django_type)
        thumbnail_field.save(file_name, suf, save=False)

        logger.debug("Done")
