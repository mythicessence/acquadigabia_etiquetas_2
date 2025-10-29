from django.shortcuts import render
from django.http import HttpResponse

def imprimirIngredientes(valor):
    # Aquí pondrás tu lógica real más adelante
    print(f"🖨️ Imprimiendo ingredientes para: {valor}")

def index(request):
    if request.method == "POST":
        valor = request.POST.get("referencia")
        imprimirIngredientes(valor)
        return HttpResponse(f"Impresión enviada para: {valor}")
    return render(request, "index.html")
