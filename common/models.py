import os
import io
import hashlib

from PIL import Image
from django.db import models
from django.core.files.uploadedfile import SimpleUploadedFile


class ImageThumbnailMixin:
    """
    Before to use, you should set IMAGE_FIELD, THUMBNAIL_FIELD, BASE_SIZE first,

    for example:

    class User(models.Model):
        name = models.CharField(max_length=100)
        avatar = models.ImageField(upload_to=settings.UPLOAD_TO, null=True, blank=True)
        thumbnail = models.Image(upload_to=settings.UPLOAD_TO, null=True, blank=True)

        IMAGE_FIELD, THUMBNAIL_FIELD, BASE_SIZE = "avatar", "thumbnail", 200

    """

    IMAGE_FIELD, THUMBNAIL_FIELD, THUMBNAIL_BASE_SIZE = None, None, 200

    def __init__(self, *args, **kwargs):
        assert self.IMAGE_FIELD is not None, "ImageThumbnailMixin should set IMAGE_FIELD first"
        assert self.THUMBNAIL_FIELD is not None, "ImageThumbnailMixin should set THUMBNAIL_FIELD first"
        super(ImageThumbnailMixin, self).__init__(*args, **kwargs)

        self.cache_old_image_md5()

    def cache_old_image_md5(self):
        if getattr(self, self.IMAGE_FIELD):
            image_md5 = self.get_image_md5(self.IMAGE_FIELD)
            setattr(self, "md5_{0}_cache".format(self.IMAGE_FIELD), image_md5)

    def get_image_md5(self, image_field):
        image = getattr(self, image_field)
        if not image or not image._file:
            return None
        md5 = hashlib.md5()
        for chunk in image.chunks():
            md5.update(chunk)
        val = md5.hexdigest()
        image.seek(0)
        return val

    def image_changed(self):
        cached_md5 = getattr(self, "md5_{0}_cache".format(self.IMAGE_FIELD), None)
        return cached_md5 != self.get_image_md5(self.IMAGE_FIELD)

    def is_image(self, field):
        f = io.BytesIO(field.read())
        try:
            Image.open(f)
            return True
        except OSError:
            return False

    def create_thumbnail(self):
        """
        Create model image field thumbnail
        """

        image_field = getattr(self, self.IMAGE_FIELD)
        thumbnail_field = getattr(self, self.THUMBNAIL_FIELD)

        if not isinstance(image_field, models.ImageField):
            return

        # image field not set or file is not image or image not changed
        if not image_field or not image_field._file or \
                not hasattr(image_field.file, "content_type") or \
                not self.is_image(image_field) or \
                not self.image_changed():
            return

        django_type = image_field.file.content_type
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
