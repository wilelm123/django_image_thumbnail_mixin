# django_image_thumbnail_mixin


Before to use, you should set IMAGE_FIELD, THUMBNAIL_FIELD, BASE_SIZE first,

for example:

class User(models.Model):
    name = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to=settings.UPLOAD_TO, null=True, blank=True)
    thumbnail = models.Image(upload_to=settings.UPLOAD_TO, null=True, blank=True)

    IMAGE_FIELD, THUMBNAIL_FIELD, BASE_SIZE = "avatar", "thumbnail", 200