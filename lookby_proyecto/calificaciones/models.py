from django.db import models

class Calificacion(models.Model):
    idCalificacion = models.AutoField(primary_key=True)
    puntuacion = models.IntegerField()
    comentario = models.TextField()
    idCliente = models.IntegerField(db_column='idCliente')
    idLocal = models.IntegerField(db_column='idLocal', null=True, blank=True)
    idProfesional = models.IntegerField(db_column='idProfesional', null=True, blank=True)

    def __str__(self):
        return f"Calificación {self.puntuacion} - Comentario ID {self.idCalificacion}"