import os
import boto3
import json
import requests
from openai import OpenAI
from srcs.pipelines import pipeline
from PyPDF2 import PdfReader


def download_from_url(url, local_path):
    if not local_path.endswith('.pdf'):
        local_path += '.pdf'  
    
    response = requests.get(url)
    if response.status_code == 200:
        with open(local_path, 'wb') as f:
            f.write(response.content)
        print(f"File successfully downloaded to {local_path}")
    else:
        print(f"Failed to download file. HTTP status code: {response.status_code}")

def parse_pdf(file_path):
    extracted_text = ""
    # Open the PDF file in binary mode
    with open(file_path, "rb") as file:
        # Create a PDF reader object
        pdf_reader = PdfReader(file)
        # Iterate through each page and extract text
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            extracted_text += page.extract_text()
    return extracted_text

def generate_questions(text):
    nlp = pipeline("question-generation")
    QnA = nlp(text)
    return QnA

def generate_answers(qna):
    options = {}
    client = OpenAI()
    for item in qna:
        answer = item['answer']
        # print(answer + '-----')
        prompt = f"generate 4 distractors for the anwser: {answer}"
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=100,
            n=1,
            temperature=0.10
        )

        generated_options = response.choices[0].text.strip().split('\n')
        all_options = [answer] + generated_options[:5]
        options[answer] = all_options

    return options

def final_results(options, qna):
    temp_dist = []
    for item in options.values():
        temp_dist.append(item)
    
    for i, entry in enumerate(qna):
        entry['distractors'] = temp_dist[i % len(temp_dist)]
    
    return qna

def json_data(result, file_name, bucket_name):
    path = f'JSON-data/{file_name}.json'
    with open(path, 'w') as file:
        json.dump(result, file, indent=4)
    
    s3 = boto3.client('s3')
    s3.upload_file(path, bucket_name, file_name + '.json')


def main(file_url):
    bucket_name = "course-materials-teachers"
    file_path = f"/Users/aboodhameed/Desktop/chatwpdf/{os.path.basename(file_url)}"

    download_from_url(file_url, file_path)
    pdf_name = os.path.basename(file_path)
    pdf = pdf_name[:-4]
    text = parse_pdf(file_path)
    qna = generate_questions(text)
    response = generate_answers(qna)
    final_response = final_results(response, qna)
    json_data(final_response, pdf, bucket_name)
    


if __name__ == "__main__":
    main()

