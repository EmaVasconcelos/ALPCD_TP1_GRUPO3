import requests
import json
import re
import typer
from datetime import datetime
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


@app.command()

def search(localizacao:str,empresa:str,n:int,export:Optional[str]=typer.Option(None,"--export","-e")):
    
    parametros={
        "limit":n,
        "api_key":API_KEY,
        "tipo":"part-time",
        "localidade":localizacao,
        "empresa":empresa
    }

    response=requests.get(BASE_URL,params=parametros,headers=header)
    if response.status_code==200:
        jobs=response.json().get("results",[])
        
        simple_jobs=[]
        for job in jobs:
            desc=job.get("description","") or job.get("body","") or ""
            desc_clean=re.sub(r'<[^<]+?>','',desc).strip()
            simple_jobs.append({
                "titulo":job.get("title",""),
                "empresa":job.get("company",{}).get("name",""),
                "descricao":desc_clean[:400],
                "data_publicacao":job.get("publishedAt",""),
                "salario":job.get("wage",""),
                "localizacao":", ".join([loc.get("name","") for loc in job.get("locations",[])]),
            })
            

        typer.echo(json.dumps(simple_jobs,indent=2,ensure_ascii=False))

        csv_export=typer.confirm("Deseja exportar para CSV?")
        if csv_export:
            export_to_csv(jobs,f"{empresa}_{localizacao}_full_time_jobs.csv")
        else:
            typer.echo("Exportação cancelada.")     
    
    else:
        typer.echo(f"Erro ao obter dados da API: {response.status_code}", err=True)
        raise typer.Exit(1)
    


##### Maria

SKILLS = [
    "Python",
    "JavaScript",
    "Java",
    "C#",
    "Ruby",
    "Go",
    "PHP",
    "Swift",
    "Kotlin",
    "TypeScript"
]

@app.command()
def skill_count(data_inicial: str, data_final: str):
    """Conta o número de ofertas de emprego que mencionam habilidades específicas dentro de um intervalo de datas."""
    parametros = {
        "api_key": API_KEY,
        "limit": 1000  # Ajuste conforme necessário
    }

    response = requests.get(BASE_URL, params=parametros, headers=header)
    if response.status_code == 200:
        jobs = response.json().get("results", [])
        
        skill_counter = {skill: 0 for skill in SKILLS}
        
        data_inicial_dt = datetime.strptime(data_inicial, "%Y-%m-%d")
        data_final_dt = datetime.strptime(data_final, "%Y-%m-%d")
        
        for job in jobs:
            pub_date_str = job.get("publishedAt", "")
            if pub_date_str:
                pub_date_dt = datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                if data_inicial_dt <= pub_date_dt <= data_final_dt:
                    description = job.get("description", "").lower()
                    for skill in SKILLS:
                        if skill.lower() in description:
                            skill_counter[skill] += 1
        
        typer.echo("Contagem de habilidades nas ofertas de emprego:")
        for skill, count in skill_counter.items():
            typer.echo(f"{skill}: {count}")
    
    else:
        typer.echo(f"Erro ao obter dados da API: {response.status_code}", err=True)
        raise typer.Exit(1)
  

if __name__ == "__main__":
    app()

