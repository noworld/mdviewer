from django.db import models


class MdLibrary(models.Model):
    file_name = models.CharField(max_length=255)
    file_version = models.IntegerField(default=1)
    file_contents = models.TextField()
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mdlibrary'
        constraints = [
            models.UniqueConstraint(fields=['file_name', 'file_version'], name='unique_file_name_version'),
        ]
        indexes = [
            models.Index(fields=['file_name'], name='idx_file_name'),
        ]
