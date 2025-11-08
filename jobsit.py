import requests
import json
import re
import typer
import datetime

app=typer.Typer()


@app.command()
def top(n:int):
    url= "https://www.itjobs.pt/api/jobs.json"
    resposta=requests.get(url)

    if resposta.status_code != 200:
        typer.echo("Erro ao aceder à API")
        raise typer.Exit(code=1)
    
    dados=resposta.json()

    recentes=dados[:n]
    typer.echo(json.dumps(recentes, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    app()


