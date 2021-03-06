from django.db import models


class CRECParserResult(models.Model):

    def __str__(self):
        if self.success:
            outcome = 'successful'
        else:
            outcome = 'failed'
        date_str = self.date.strftime('%Y-%m-%d')
        return 'CREC Issued Date: {0}, S3 key: {1}, parsing {2}: {3}'.format(
            date_str, self.crec_s3_key, outcome, self.message
        )

    date = models.DateField()
    success = models.BooleanField()
    message = models.TextField()
    crec_s3_key = models.CharField(max_length=200)
