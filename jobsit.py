import requests
import json
import re
import typer
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
        #Permite subcomandos explícitos (ex.: python jobsit.py top 5).
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
    


@app.command()
def type(jobid: str):
    """Extrai o regime de trabalho (remoto/híbrido/presencial/outro) de um anúncio específico a partir job ID."""
    
    URL = "https://api.itjobs.pt/job/get.json"
    parametros = {"api_key":API_KEY,"id":jobid}

    response = requests.get(URL, params=parametros, headers=header)

    if response.status_code != 200:
        typer.echo(f"Erro ao obter dados do job ID {jobid}: {response.status_code}", err=True)
        raise typer.Exit(1)

    job = response.json()

    if not job or ("title" not in job and "description" not in job and "body" not in job):
        typer.echo(f"Erro: job ID {jobid} inválido ou não encontrado.", err=True)
        raise typer.Exit(1)

    descricao = job.get("description","") or ""
    corpo = job.get("body","") or ""
    titulo=job.get("title","") or ""
    texto = f"{titulo} {descricao} {corpo}"
    texto_final = re.sub(r'<[^<]+?>', '', texto).lower().replace('\n', ' ').strip()

    remoto = re.search(r"(remoto|remote|teletrabalho|home office)", texto_final)
    presencial = re.search(r"(presencial|escritório|office)", texto_final)
    hibrido = re.search(r"(híbrido|hybrid)", texto_final)
    
    if (remoto and presencial) or hibrido:
        regime = "híbrido"
    elif remoto:
        regime = "remoto"
    elif presencial:
        regime = "presencial"
    else:
        regime = "outro"

    typer.echo(f"Regime de trabalho: {regime}")
   


@app.command()
def skills(skills: List[str], data_inicial: str, data_final: str):
    """Lista os trabalhos que requerem uma determinada lista de skills num período de tempo específico e opcionalmente salva em CSV."""
    
    parametros = {
        "api_key": API_KEY,
        "skills": ",".join(skills),
        "data_inicial": data_inicial,
        "data_final": data_final
    }

    response = requests.get(BASE_URL, headers=header, params=parametros)
    if response.status_code == 200:
        jobs = response.json().get("results", [])
        print(json.dumps(jobs, indent=2))
        
        csv_export=typer.confirm("Deseja exportar para CSV?")
        if csv_export:
            export_to_csv(jobs,"skill_jobs.csv")
    else:
        print(f"Erro: {response.status_code}")





#parte da mafalda



@app.command()
def statistics(export:Optional[str]=typer.Option(None,"--export","-e")):
    
    parametros={
        "limit":200,
        "api_key":API_KEY
    }

    response=requests.get(BASE_URL,params=parametros,headers=header)

    if response.status_code!=200:
        typer.echo("Erro ao obter os dados da API.")
        raise typer.Exit(1)
    
    jobs=response.json().get("results",[])
    estatisticas={}

    for job in jobs:
        titulo=job.get("title","")
        zonas=[loc.get("name","") for loc in job.get("locations",[])]

        for zona in zonas:
            chave=(zona,titulo)
            estatisticas[chave]=estatisticas.get(chave,0)+1

    typer.echo("Estatisticas de empregos por zona e tipo:")
    for (zona,titulo),contagem in estatisticas.items():
        typer.echo(f"{zona:<20} - {titulo:<40}: {contagem} empregos")


    csv_export=typer.confirm("Deseja exportar as estatísticas para CSV?")

    if csv_export:
        filename="estatisticas_empregos.csv"
        with open(filename,mode='w',newline='',encoding='utf-8') as csvfile:
            writer=csv.writer(csvfile)
            writer.writerow(["zona","tipo de emprego","contagem"])
            for (zona,titulo),contagem in estatisticas.items():
                writer.writerow([zona,titulo,contagem])

        typer.echo(f"Estatísticas exportadas para {filename}")
    
    else:
        typer.echo("Nao foi exportado nenhum csv.")



if __name__ == "__main__":
    app()