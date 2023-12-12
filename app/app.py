from flask import Flask
from flask_restful import Resource, Api, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ToDos.db'
db = SQLAlchemy(app)


class ToDoModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(500), nullable=False)


task_post_args = reqparse.RequestParser()
task_post_args.add_argument("task",
                            type=str,
                            help='Task is required',
                            required=True)
task_post_args.add_argument("summary",
                            type=str,
                            help='summary is required',
                            required=True)

task_update_args = reqparse.RequestParser()
task_update_args.add_argument("task",
                              type=str)
task_update_args.add_argument("summary",
                              type=str)

resource_fields = {
    'id': fields.Integer,
    'task': fields.String,
    'summary': fields.String
}


class ToDoList(Resource):
    def get(self):
        with app.app_context():
            tasks = ToDoModel.query.all()
            todos = {}
            for task in tasks:
                todos[task.id] = {'task': task.task, 'summary': task.summary}
            return todos, 200


class ToDo(Resource):
    @marshal_with(resource_fields)
    def get(self, todo_id):
        with app.app_context():
            task = ToDoModel.query.filter_by(id=todo_id).first()
            if not task:
                return {"error": "Could not find task id"}, 404
            return task, 200

    @marshal_with(resource_fields)
    def post(self, todo_id):
        with app.app_context():
            args = task_post_args.parse_args()
            existing_task = ToDoModel.query.get(todo_id)

            if existing_task:
                abort(409, message='Task already exists')

            try:
                todo = ToDoModel(id=todo_id,
                                 task=args['task'],
                                 summary=args['summary'])

                db.session.add(todo)
                db.session.commit()

                return {'message': 'Task successfully created'}, 201

            except Exception as e:
                db.session.rollback()
                abort(500,
                      message=f'Failde to create new task. Error: {str(e)}')

            finally:
                db.session.close()

    @marshal_with(resource_fields)
    def put(self, todo_id):
        args = task_update_args.parse_args()

        with app.app_context():
            task = ToDoModel.query.filter_by(id=todo_id).first()

            if not task:
                abort(404, message='Task does not exist, impossible to update')

            if args['task']:
                task.task = args["task"]
            if args['summary']:
                task.summary = args["summary"]

            try:
                db.session.commit()
                db.session.refresh(task)

                return task, 200

            except Exception as e:
                db.session.rollback()
                abort(500, message=f'Failed to update task. Error: {str(e)}')

            finally:
                db.session.close()

    def delete(self, todo_id):
        with app.app_context():
            task = ToDoModel.query.filter_by(id=todo_id).first()

            if not task:
                return {"error": "Task with ID {} does not exist.".format(todo_id)}, 404

            try:
                db.session.delete(task)
                db.session.commit()
                return {'message': 'Task successfully deleted'}, 200

            except Exception as e:
                db.session.rollback()
                abort(500, 
                      message=f'Failed to delete task. Error: {str(e)}')

            finally:
                db.session.close()


api.add_resource(ToDo, '/todos/<int:todo_id>')
api.add_resource(ToDoList, '/todos')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
