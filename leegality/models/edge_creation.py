from django.db import models

from .node_creation import Node


class Edge(models.Model):
    id = models.AutoField(primary_key=True)
    source = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        db_column='source_id',
        related_name='source_id',
    )
    destination = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        db_column='destination_id',
        related_name='destination_id',
    )
    latency = models.FloatField()

    class Meta:
        managed = False
        db_table = 'edge_creater'
        unique_together = (('source', 'destination'),)
