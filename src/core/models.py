from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Aluno(models.Model):
    nome = models.CharField(max_length=255)

    def __str__(self):
        return self.nome


class Curso(models.Model):
    nome = models.CharField(max_length=255)

    def __str__(self):
        return self.nome


class Matricula(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="matriculas")
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="matriculas")

    class Meta:
        unique_together = ("aluno", "curso")

    def __str__(self):
        return f"{self.aluno} - {self.curso}"


class Nota(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name="notas")
    valor = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.matricula}: {self.valor}"
