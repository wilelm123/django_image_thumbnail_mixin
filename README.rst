django_image_thumbnail_mixin
===========================

Before to use, you should set IMAGE_FIELD, THUMBNAIL_FIELD, THUMBNAIL_BASE_SIZE first,


Usage:

.. code-block:: python

    from django.db import models
    from project.common.models import ImageThumbnailMixin


    class User(models.Model, ImageThumbnailMixin):
        name = models.CharField(max_length=100)
        avatar = models.ImageField(upload_to=settings.UPLOAD_TO, null=True, blank=True)
        thumbnail = models.Image(upload_to=settings.UPLOAD_TO, null=True, blank=True)

        IMAGE_FIELD, THUMBNAIL_FIELD, THUMBNAIL_BASE_SIZE = "avatar", "thumbnail", 200

        def save(self, *args, **kwargs):
            self.create_thumbnail()
            return super().save(*args, **kwargs)
