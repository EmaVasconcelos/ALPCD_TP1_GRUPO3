import requests
import json
import re
import typer
import datetime
import csv
from typing import Optional,List

app=typer.Typer()

BASE_URL="https://api.itjobs.pt/job/list.json"
API_KEY="0e1d382aea19663d13db0633833b9b40"

header= {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
      


def export_to_csv(jobs:list, filename:str):
    
    fieldnames=["titulo","empresa","descricao","data_publicacao","salario","localizacao"]
 
    with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer=csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for job in jobs:
            row={
                "titulo": job.get("title", ""),
                "empresa": job.get("company", {}).get("name", ""),
                "descricao": re.sub('<[^<]+?>', '', job.get("description", "")),
                "data_publicacao": job.get("publishedAt", ""),
                "salario": job.get("wage", ""),
                "localizacao": ", ".join([loc.get("name", "") for loc in job.get("locations", [])])
            }
            writer.writerow(row)


    typer.echo(f"Empregos exportados para {filename}")

@app.callback(invoke_without_command=True)
def main():
    """Permite subcomandos explícitos (ex.: python jobsit.py top 5)."""
    pass

@app.command()
def top(n:int, export:Optional[str]=typer.Option(None,"--export","-e")):

    parametros={
        "limit":n,
        "api_key":API_KEY
    }
    
    response=requests.get(BASE_URL,params=parametros,headers=header)  

    if response.status_code==200:


        jobs=response.json().get("results",[])
        print(f"\nTop {n} empregos mais recentes:")     
        for job in jobs:
            print(f"{job.get('title','N/A')}")
      
        
        csv_export=typer.confirm("Deseja exportar para CSV?")
        if csv_export:
            export_to_csv(jobs,"recent_jobs.csv")
        
        else:
            typer.echo("Exportação cancelada.")
    
    else:
        typer.echo(f"Erro ao obter dados da API: {response.status_code}", err=True)
        raise typer.Exit(1)


  

if __name__ == "__main__":
    app()


