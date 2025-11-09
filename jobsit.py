import requests
import json
import re
import typer
import datetime
import csv
from typing import Optional

app=typer.Typer()
header= {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.itjobs.pt/"
    
}
      


base_url="https://www.itjobs.pt/api/offers"

def export_to_csv(jobs:list, filename:str):
    if not jobs:
        typer.echo("Não há empregos para exportar.")
        return
    
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




@app.command()
def top(n:int,export:Optional[str]=typer.Option(None,"--export","-e")):

    try:
        response=requests.get(f"{base_url}",params={"limit":n},headers=header)  
        response.raise_for_status()
      
        typer.echo(f"Status Code: {response.status_code}")
        typer.echo(f"Content-Type: {response.headers.get('Content-Type')}")
        typer.echo(f"Primeiros 500 caracteres da resposta:")
        typer.echo(response.text[:500])
        typer.echo("=" * 50)


        data=response.json()
        jobs=data.get("results", [])
      
        jobs=jobs[:n]

        typer.echo(f"Top {n} empregos mais recentes:")
        typer.echo(json.dumps(jobs, indent=2, ensure_ascii=False))
      
        if export:
         export_to_csv(jobs, export)


    except requests.RequestException as e:
        typer.echo(f"Erro ao aceder à API: {e}", err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()


