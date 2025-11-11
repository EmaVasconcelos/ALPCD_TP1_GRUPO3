import requests
import json
import re
import typer
from datetime import datetime
from dateutil import parser
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
def search(localidade:str,empresa:str,n:int,export:Optional[str]=typer.Option(None,"--export","-e")):
    
    parametros={
        "limit":n,
        "api_key":API_KEY,
        "tipo":"part-time",
        "localizacao":localidade,
        "empresa":empresa
    }

    response=requests.get(BASE_URL,params=parametros,headers=header)
    if response.status_code==200:
        jobs=response.json().get("results",[])
        
        simple_jobs=[]
        for job in jobs:
            locs=[loc.get("name","") for loc in job.get("locations",[])]
            if not any(localidade.lower() in l.lower() for l in locs):
                continue


            desc=job.get("description","") or job.get("body","") or ""
            desc_clean=re.sub(r'<[^<]+?>','',desc).strip()
            simple_job={
                "titulo":job.get("title",""),
                "empresa":job.get("company",{}).get("name",""),
                "descricao":desc_clean[:400],
                "data_publicacao":job.get("publishedAt",""),
                "salario":job.get("wage",""),
                "localizacao":", ".join([loc.get("name","") for loc in job.get("locations",[])]),
            }
            simple_jobs.append(simple_job)

        typer.echo(json.dumps(simple_jobs,indent=2,ensure_ascii=False))

        csv_export=typer.confirm("Deseja exportar para CSV?")
        if csv_export:
            export_to_csv(jobs,f"{empresa}_{localidade}_full_time_jobs.csv")
        else:
            typer.echo("Exportação cancelada.")     
    
    else:
        typer.echo(f"Erro ao obter dados da API: {response.status_code}", err=True)
        raise typer.Exit(1)
    


##### Maria
   
SKILLS = [
    "Python", "JavaScript", "Java", "C#", "Ruby",
    "Go", "PHP", "Swift", "Kotlin", "TypeScript"
]

@app.command()
def skill_count(data_inicial: str, data_final: str):
    """Conta o número de ofertas de emprego que mencionam habilidades específicas dentro de um intervalo de datas."""
    params = {
        "api_key": API_KEY,
        "limit": 1000}
    response = requests.get(BASE_URL, params=params, headers=header)

    if response.status_code != 200:
        typer.echo(f"Erro ao obter dados da API: {response.status_code}", err=True)
        raise typer.Exit(1)

    jobs = response.json().get("jobs", [])
    skill_counter = {skill: 0 for skill in SKILLS}

    data_inicial_dt = datetime.strptime(data_inicial, "%Y-%m-%d")
    data_final_dt = datetime.strptime(data_final, "%Y-%m-%d")

    for job in jobs:
        pub_date_str = job.get("published", "")
        if pub_date_str:
            try:
                pub_date_dt = parser.parse(pub_date_str)
            except:
                continue

            if data_inicial_dt <= pub_date_dt <= data_final_dt:
                description = job.get("description", "").lower()
                for skill in SKILLS:
                    if skill.lower() in description:
                        skill_counter[skill] += 1

    resultado = sorted(skill_counter.items(), key=lambda x: x[1], reverse=True)
    print(json.dumps([{skill: count} for skill, count in resultado if count > 0], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    app()

