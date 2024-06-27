from django.db import models

# Create your models here.
class Character(models.Model):
    name = models.CharField(max_length=30)
    house_name = models.CharField(max_length=30)
    age = models.IntegerField()
    status = models.CharField(max_length=40, default='alive')
    # status2 = models.BooleanField(default=False)



    def __str__(self):
        return f"{self.name} {self.house_name}"

    class Meta:
        verbose_name = 'Character'
        ordering = ['house_name', '-age']



