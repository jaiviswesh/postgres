from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import json
import os

app = Flask(__name__)
# Be more specific with CORS to allow all origins for API routes
CORS(app, resources={r"/api/*": {"origins": "*"}})

database_url = os.getenv('DATABASE_URL', 'postgresql://flaskuser:flaskpass@postgres/flask_crud_db')



app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define Models
class Chapter(db.Model):
    __tablename__ = 'chapter_table'
    id = db.Column(db.Integer, primary_key=True)
    chaptername = db.Column(db.String, nullable=False)
    summary = db.Column(db.String, nullable=True)
    problems_and_solutions = db.Column(db.Text, nullable=True)  # Store as JSON string

class Subtopic(db.Model):
    __tablename__ = 'subtopic_table'
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter_table.id'), nullable=False)
    subtopicname = db.Column(db.String, nullable=False)
    exercises = db.Column(db.Text, nullable=True)
    experiments = db.Column(db.Text, nullable=True)
    figures = db.Column(db.Text, nullable=True)
    tables = db.Column(db.Text, nullable=True)

    chapter = db.relationship('Chapter', backref=db.backref('subtopics', cascade='all, delete-orphan'))


# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/chapters', methods=['POST'])
def create_chapter():
    try:
        data = request.get_json()
        new_chapter = Chapter(
            chaptername=data.get('chapter_name', ''),
            summary=data.get('summary', ''),
            problems_and_solutions=json.dumps(data.get('problems_and_solutions', []))
        )
        db.session.add(new_chapter)
        db.session.flush()  # to get new_chapter.id

        for subtopic_data in data.get('subtopics', []):
            sub = Subtopic(
                chapter_id=new_chapter.id,
                subtopicname=subtopic_data.get('subtopic_name', ''),
                exercises=json.dumps(subtopic_data.get('exercises', [])),
                experiments=json.dumps(subtopic_data.get('experiments', [])),
                figures=json.dumps(subtopic_data.get('figures', [])),
                tables=json.dumps(subtopic_data.get('tables', []))
            )
            db.session.add(sub)

        db.session.commit()
        return jsonify({'message': 'Chapter created'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/chapters', methods=['GET'])
def get_chapters():
    chapters = Chapter.query.all()
    results = []
    for chapter in chapters:
        subtopic_list = []
        # Use the relationship to get subtopics - it's easier and correct
        for sub in chapter.subtopics:
            subtopic_list.append({
                'subtopic_name': sub.subtopicname,
                'exercises': json.loads(sub.exercises or '[]'),
                'experiments': json.loads(sub.experiments or '[]'),
                'figures': json.loads(sub.figures or '[]'),
                'tables': json.loads(sub.tables or '[]')
            })
        results.append({
            'id': chapter.id,
            'chapter_name': chapter.chaptername,
            'summary': chapter.summary,
            'problems_and_solutions': json.loads(chapter.problems_and_solutions or '[]'),
            'subtopics': subtopic_list
        })
    return jsonify(results)


@app.route('/api/chapters/<int:chapter_id>', methods=['GET'])
def get_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({'error': 'Not found'}), 404
        
    subtopic_list = []
    for sub in chapter.subtopics:
        subtopic_list.append({
            'subtopic_name': sub.subtopicname,
            'exercises': json.loads(sub.exercises or '[]'),
            'experiments': json.loads(sub.experiments or '[]'),
            'figures': json.loads(sub.figures or '[]'),
            'tables': json.loads(sub.tables or '[]')
        })
    return jsonify({
        'id': chapter.id,
        'chapter_name': chapter.chaptername,
        'summary': chapter.summary,
        'problems_and_solutions': json.loads(chapter.problems_and_solutions or '[]'),
        'subtopics': subtopic_list
    })

@app.route('/api/chapters/<int:chapter_id>', methods=['PUT'])
def update_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({'error': 'Chapter not found'}), 404

    data = request.get_json()
    chapter.chaptername = data.get('chapter_name', chapter.chaptername)
    chapter.summary = data.get('summary', chapter.summary)
    chapter.problems_and_solutions = json.dumps(data.get('problems_and_solutions', []))

    for sub in chapter.subtopics:
        db.session.delete(sub)

    # Add new subtopics with the correct chapter_id
    for subtopic_data in data.get('subtopics', []):
        subtopic = Subtopic(
            chapter_id=chapter.id, # Use the ID
            subtopicname=subtopic_data.get('subtopic_name', ''),
            exercises=json.dumps(subtopic_data.get('exercises', [])),
            experiments=json.dumps(subtopic_data.get('experiments', [])),
            figures=json.dumps(subtopic_data.get('figures', [])),
            tables=json.dumps(subtopic_data.get('tables', []))
        )
        db.session.add(subtopic)

    db.session.commit()
    return jsonify({'message': 'Chapter updated successfully'}), 200


@app.route('/api/chapters/<int:chapter_id>', methods=['DELETE'])
def delete_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({'error': 'Not found'}), 404

    db.session.delete(chapter)
    db.session.commit()
    return jsonify({'message': 'Chapter and related subtopics deleted'})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=True, reloader_type='stat')
