from django.db import models


class Book(models.Model):
    class CoverChoices(models.TextChoices):
        HARD = "hard", "Hard"
        SOFT = "soft", "Soft"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(
        max_length=20,
        choices=CoverChoices.choices,
        default=CoverChoices.HARD
    )
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return (f"{self.title} - Cover: {self.get_cover_display()}, "
                f"Daily fee: ${self.daily_fee}")
