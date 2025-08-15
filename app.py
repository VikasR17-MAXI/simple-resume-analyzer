from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from docx import Document
from PyPDF2 import PdfReader

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
TOP_RESUMES = 3

def calculate_ats_score(resume_text, job_description):
    score = 0
    jd_keywords = set(job_description.lower().split())
    resume_words = set(resume_text.lower().split())
    
    keyword_match = len(jd_keywords & resume_words) / max(len(jd_keywords), 1)
    score += keyword_match * 0.6
    
    if len(resume_text.split()) > 300:
        score += 0.2
    
    skills = ['python', 'java', 'sql', 'machine learning', 'data science']
    skill_count = sum(1 for skill in skills if skill in resume_text.lower())
    score += min(skill_count * 0.05, 0.2)
    
    return round(min(score, 1.0), 2)

def generate_feedback(resume_text, job_description):
    feedback = []
    ats_score = calculate_ats_score(resume_text, job_description)
    
    if ats_score < 0.5:
        feedback.append("Low ATS score: many keywords missing. Add relevant skills.")
    elif ats_score < 0.75:
        feedback.append("Moderate ATS score: improve keyword relevance and completeness.")
    else:
        feedback.append("High ATS score: strong match! Tailor further for best impact.")
    
    if len(resume_text) < 500:
        feedback.append("Your resume is quite short. Consider adding more detail about your skills and experience.")
    if 'project' not in resume_text.lower():
        feedback.append("Include any significant projects or achievements for more impact.")
    if 'python' in job_description.lower() and 'python' not in resume_text.lower():
        feedback.append("The job mentions Python, but your resume does not. Highlight your Python skills.")
    
    return feedback

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    message = ""

    if request.method == 'POST':
        try:
            resume_files = request.files.getlist('resumeFile')
            job_description = request.form.get('resumeText', '').strip()

            if not resume_files or not job_description:
                return render_template('app.html', message="Please upload at least one resume and enter a job description.")

            uploaded_resumes = []
            filenames = []
            resume_feedback = []
            ats_scores = []

            for file in resume_files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(save_path)

                    resume_text = extract_text(save_path)
                    uploaded_resumes.append(resume_text)
                    filenames.append(filename)
                    resume_feedback.append(generate_feedback(resume_text, job_description))
                    ats_scores.append(calculate_ats_score(resume_text, job_description))

            if not uploaded_resumes:
                return render_template('app.html', message="No valid resumes were uploaded.")

            documents = [job_description] + uploaded_resumes
            tfidf = TfidfVectorizer(stop_words='english').fit_transform(documents)
            similarities = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()

            top_indices = similarities.argsort()[-TOP_RESUMES:][::-1]
            results = [
                {
                    "filename": filenames[i],
                    "score": round(float(similarities[i]), 2),
                    "ats_score": ats_scores[i],
                    "feedback": resume_feedback[i]
                }
                for i in top_indices
            ]

            message = "Top matching resumes:"

        except Exception as e:
            message = f"An error occurred: {str(e)}"

    return render_template('app.html', results=results, message=message)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'docx', 'txt'}

def extract_text(filepath):
    ext = filepath.rsplit('.', 1)[1].lower()
    text = ""
    if ext == 'txt':
        with open(filepath, 'r', errors='ignore') as f:
            text = f.read()
    elif ext == 'docx':
        doc = Document(filepath)
        text = "\n".join([para.text for para in doc.paragraphs])
    elif ext == 'pdf':
        reader = PdfReader(filepath)
        text = "\n".join([page.extract_text() or '' for page in reader.pages])
    return text

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
