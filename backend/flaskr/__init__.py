import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    RESULTS_PER_PAGE = 10

    def paginate_questions(request,selection):
      page = request.args.get('page',1,type=int)
      start = (page-1)*RESULTS_PER_PAGE
      end = start+RESULTS_PER_PAGE
      formatted_questions = [question.format() for question in selection]
      return formatted_questions[start:end]

    cors = CORS(app,resources={r"/*":{"origins":"*"}})

    @app.after_request
    def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
      return response

    @app.route('/categories')
    def get_categories():
      categories = Category.query.order_by(Category.type).all()

      if(len(categories)==0):
        abort(404)
        
      formatted_categories = {category.id:category.type for category in categories}
      return jsonify({
        "categories":formatted_categories,
        "success":True
        })

    @app.route('/questions')
    def get_questions():

      questions = Question.query.all()
      current_questions = paginate_questions(request,questions)
      all_categories = Category.query.order_by(Category.type).all()

      if(len(all_categories)==0):
        abort(404)
      if(len(current_questions)==0):
        abort(404)
    
      return jsonify({
          "success":True,
          "questions":current_questions,
          "total_questions":len(Question.query.all()),
          "categories":{category.id:category.type for category in all_categories},
          "current_category":None
          })

    @app.route('/questions/<question_id>',methods=['DELETE'])
    def delete_questions(question_id):

      question = Question.query.filter(Question.id==question_id).one_or_none()

      if question is None:
        abort(404)
      else:
        try:
          question.delete()
          return jsonify({
            "success":True,
            "deleted_question_id":question_id
          })
        except:
          abort(404)

    @app.route('/questions',methods=["POST"])
    def create_questions():
      body = request.get_json()

      new_question = body.get('question',None)
      new_answer = body.get('answer',None)
      new_difficulty = body.get('difficulty',None)
      new_category = body.get('category',None)
    
      try:
        question = Question(question=new_question,answer=new_answer,difficulty=new_difficulty,category=new_category)
        question.insert()
        return jsonify({
          "success":True,
          "created_question":question.id
        })
      except:
        abort(404)

    @app.route('/questions/search',methods=["POST"])
    def search_questions():
      body=request.get_json()
      search = body.get('searchTerm',None)

      if(search):
        try:
          selection = Question.query.filter(Question.question.ilike(f'%{search}%')).all()
          current_questions = paginate_questions(request,selection)
          return jsonify({
              "success":True,
              "questions":current_questions,
              "totalQuestions":len(selection),
              "currentCategory":None
            })
        except:
          abort(404)
      
      abort(404)
 
    @app.route('/categories/<category_id>/questions',methods=["GET"])
    def get_questions_by_category(category_id):

        try:
          questions = Question.query.filter(Question.category == str(category_id)).all()

          return jsonify({
              'success': True,
              'questions': [question.format() for question in questions],
              'total_questions': len(questions),
              'current_category': category_id
          })
        except:
            abort(404)

    @app.route('/quizzes',methods=["POST"])
    def play_quiz():

        try:

            body = request.get_json()

            if not ('quiz_category' in body and 'previous_questions' in body):
                abort(422)

            category = body.get('quiz_category')
            previous_questions = body.get('previous_questions')

            if category['type'] == 'click':
                available_questions = Question.query.filter(
                    Question.id.notin_((previous_questions))).all()
            else:
                available_questions = Question.query.filter_by(
                    category=category['id']).filter(Question.id.notin_((previous_questions))).all()

            new_question = available_questions[random.randrange(
                0, len(available_questions))].format() if len(available_questions) > 0 else None

            return jsonify({
                'success': True,
                'question': new_question
            })
        except:
            abort(422)
  
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    return app

    