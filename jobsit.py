import requests
import json
import re
import typer
import csv
from typing import Optional,List
from collections import Counter
from bs4 import BeautifulSoup

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
    

URL = "https://api.itjobs.pt/job/get.json"

@app.command()
def type(jobid: str):
    """Extrai o regime de trabalho (remoto/híbrido/presencial/outro) de um anúncio específico a partir job ID."""
    
    parametros = {"api_key":API_KEY,"id":jobid}

    response = requests.get(URL, params=parametros, headers=header)

    if response.status_code != 200:
        typer.echo(f"Erro ao obter dados do job ID {jobid}: {response.status_code}")
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
    
    parametros = {"api_key": API_KEY,"skills": ",".join(skills)}

    response = requests.get(BASE_URL, headers=header, params=parametros)
    if response.status_code == 200:
        jobs = response.json().get("results", [])
        print(json.dumps(jobs, indent=2))
        
        csv_export=typer.confirm("Deseja exportar para CSV?")
        if csv_export:
            export_to_csv(jobs,"skill_jobs.csv")
    else:
        print(f"Erro: {response.status_code}")


TEAMLYZER_HEADER = {"User-Agent": "Mozilla/5.0 (compatible; TeamlyzerScraper/1.0)"}

@app.command()
def get(jobid: str, export: bool = typer.Option(False, "--export", "-e")):
    """obter informações sobre um jobID e adicionar informações acerca da empresa."""
  
    params = {"api_key": API_KEY, "id": jobid}
    response = requests.get(URL, params=params, headers=header)

    if response.status_code != 200:
        typer.echo(f"Erro ao obter dados do job ID {jobid}: {response.status_code}")
        raise typer.Exit(1)

    job = response.json()
    company = job.get("company", {}).get("name", "").strip()
    if not company:
        typer.echo("Não existe nenhuma empresa relacionada a este anúncio.")
        raise typer.Exit(1)

    nome_empresa = company.lower().replace(" ", "-")
    company_url = f"https://pt.teamlyzer.com/companies/{nome_empresa}"

    teamlyzer_rating = None
    teamlyzer_description = None
    teamlyzer_salary = None 
    teamlyzer_benefits = None
    
    try:
        response_teamlyzer= requests.get(company_url, headers=TEAMLYZER_HEADER)
        response_teamlyzer.raise_for_status()

        soup = BeautifulSoup(response_teamlyzer.text, "html.parser")
    
        rating = ((soup.find("span", class_="text-center c_rating")) or (soup.find("span", class_="text-center aa_rating"))) 

        if rating:
            teamlyzer_rating = rating.get_text(strip=True)

        description = soup.find("div", class_="ellipsis center_mobile")
        if description:
            teamlyzer_description = description.get_text(strip=True)

        reviews = soup.find("div", class_="col-lg-12 box_background_style_overall voffset2")
        if reviews:
            salary_icone= reviews.find("i", class_="fa fa-eur")
            if salary_icone:
                box= salary_icone.find_parent("div", class_="panel mini-box")
                if box:
                    salary_box = box.find("div", class_="box-info")
                    if salary_box:
                        salary = salary_box.find("p", class_="size-h2")
                        if salary:
                            teamlyzer_salary = " ".join(salary.get_text(strip=True).split()[:3])     
    
    except requests.RequestException:
        typer.echo("Erro ao aceder ao Teamlyzer.", err=True)
        raise typer.Exit(1)

    benefits_url= f"https://pt.teamlyzer.com/companies/{nome_empresa}/benefits-and-values"
    try:
        response_benefits= requests.get(benefits_url, headers=TEAMLYZER_HEADER)
        response_benefits.raise_for_status()
    
        soup_benefits = BeautifulSoup(response_benefits.text, "html.parser")
        
        teamlyzer_benefits = {}
        area=None
        
        benefits_blocks = soup_benefits.find_all("div", class_="col-lg-12 voffset3 divider_benefits")
        if not benefits_blocks:
            typer.echo("Empresa sem página de benefícios no Teamlyzer.")
            teamlyzer_benefits = None
        else:
            for block in benefits_blocks:
                block_area=block.find("h3")
                if block_area and block_area.find("b"):
                    area = block_area.find("b").get_text(strip=True)
                    teamlyzer_benefits[area] = []
                
                benefits = block.find_all("div", class_="flex_details")
                for benefit in benefits:
                    benefits_text=benefit.get_text(strip=True)
                    if benefits_text and area:
                        teamlyzer_benefits[area].append(benefits_text)

        benefits_lines = []
        for tema, beneficios in teamlyzer_benefits.items():
            if beneficios:
                beneficios_str = ", ".join(beneficios)
                benefits_lines.append(f"{tema}:{beneficios_str}")
        teamlyzer_benefits= " | ".join(benefits_lines) 

    except requests.RequestException:
        typer.echo(f"Erro ao aceder à página de benefícios do Teamlyzer.", err=True)
        teamlyzer_benefits = None

    resultado = {
        "job_id": jobid,
        "job_title": job.get("title", ""),
        "company_name": company,
        "teamlyzer_rating": teamlyzer_rating,
        "teamlyzer_description": teamlyzer_description,
        "teamlyzer_benefits": teamlyzer_benefits,
        "teamlyzer_salary": teamlyzer_salary
    }
    
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    exportar_csv = typer.confirm("Deseja exportar o resultado para CSV?")

    if exportar_csv:
        filename = f"job_teamlyzer_{jobid}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["job_id", "job_title", "company_name", "teamlyzer_rating", "teamlyzer_description", "teamlyzer_salary", "teamlyzer_benefits"])
            writer.writerow([
                jobid, job["title"], company, 
                teamlyzer_rating or "", teamlyzer_description or "", 
                teamlyzer_salary or "", teamlyzer_benefits or ""
            ])
        typer.echo(f"CSV exportado com sucesso: {filename}") 
    else:
        typer.echo("Exportação não foi concluída")
   
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


BASE_URL_TEAMLYZER = "https://pt.teamlyzer.com/companies/jobs"

@app.command()
def list_skills(job: str):

    """Lista as top 10 skills pedidas no website Teamlyzer para um determinado trabalho."""

    url = f"https://pt.teamlyzer.com/companies/jobs?tags=python&order=most_relevant"

    try:
        response = requests.get(url, headers=header)
        response.raise_for_status()
    except requests.RequestException as e: 
        typer.echo(f"Erro ao obter dados do Teamlyzer: {e}", err=True)
        raise typer.Exit()

    # Parse HTML
    soup = BeautifulSoup(response.text, "html.parser")

    all_skills = []

    tag_links = soup.select("div.tags a[href*='/companies/?tags=']")
    for link in tag_links:
        skill = link.get_text(strip=True).lower()
        if skill:
            all_skills.append(skill)

    if not all_skills:
        typer.echo("Nenhuma skill encontrada para este trabalho.")
        raise typer.Exit()

    # Contar ocorrências
    counter = Counter(all_skills)
    top10 = counter.most_common(10)

    resultado = [{"skill": skill, "count": count} for skill, count in top10]

    print(json.dumps(resultado, indent=2, ensure_ascii=False))

    exportar_csv = typer.confirm("Deseja exportar o resultado para CSV?")

    if exportar_csv:
        filename = f"top10_skills_{job}.csv"
        with open(filename, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["skill", "count"])
            writer.writeheader()
            writer.writerows(resultado)

        typer.echo(f"CSV exportado com sucesso: {filename}")
    else:
        typer.echo("Exportação cancelada.")

if __name__ == "__main__":
    app()