from flask import Flask, request
from flask_restplus import Api, Resource, fields, reqparse
from werkzeug.contrib.fixers import ProxyFix
from datetime import datetime
import json
from functools import wraps
import MySQLdb

authorizations = {
    'apikey' : {
        'type' : 'apiKey',
        'in' : 'header',
        'name' : 'X-API-KEY'
    }
}

db = MySQLdb.connect(host="localhost", user="shiva", db="mysql", passwd="$$Shiva123")


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version='1.0', title='TodoMVC API',
    description='A simple TodoMVC API', authorizations=authorizations,
)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        token = None

        if 'X-API-KEY' in request.headers:
            token = request.headers['X-API-KEY']

        if not token:
            return {'message' : 'Token is missing.'}, 401

        if token != 'mytoken':
            return {'message' : 'Your token is wrong!!!'}, 401

        print('TOKEN: {}'.format(token))
        return f(*args, **kwargs)

    return decorated

ns = api.namespace('todos', description='TODO operations')

# class StatusItem(fields.Raw):
#     def format(self, value):
#         if value >= 1 :
#             if value >= 2 :
#                 return "finished"
#             else:
#                 return "in progress"
#         else:
#             return "not started"

todo = api.model('Todo', {
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details'),
    'due_by': fields.Date(required=True, description='The date by when the task should be finished'),
    'status': fields.String(required=True,description='Progress status of task'),
    # 'status': StatusItem(attribute='flags',description='Progress status of task'),
})

status = api.model('status',{
    'status':fields.String(required=True),
})


class TodoDAO(object):
    def __init__(self):
        self.counter = 0
        self.todos = []

        cursor = db.cursor()
        cursor.execute("drop table if exists Tasks")

        tab_query = "create table Tasks( id int, task varchar(30), due_by date, status varchar(15), primary key (id))"
        try:
            cursor.execute(tab_query)
            db.commit()
        except Exception as e:
            print("Error in create table")
            db.rollback()

    def get(self, id):
        for todo in self.todos:
            if todo['id'] == id:
                return todo
        api.abort(404, "Todo {} doesn't exist".format(id))
    
    def getDate(self, date):
        todo_list = []
        for todo in self.todos:
            print(str(todo['due_by']), date)
            if str(todo['due_by']) == date:
                todo_list.append(todo)
        if len(todo_list):
            return todo_list
        api.abort(404, "Todo {} doesn't exist".format(date))

    def getoverDate(self):
        todo_list = []
        today = datetime.today().strftime('%Y-%m-%d')
        for todo in self.todos:
            print(str(todo['due_by']), today)
            if todo['due_by'] < today:
                todo_list.append(todo)
        if len(todo_list):
            return todo_list
        api.abort(404, "Todo {} doesn't exist".format(today))

    def getFinished(self):
        todo_list = []
        for todo in self.todos:
            print(todo['status'])
            if todo['status'] == "finished":
                todo_list.append(todo)
        if len(todo_list):
            return todo_list
        api.abort(404, "Todo {} doesn't exist".format("finished"))

    def create(self, data):
        todo = data
        todo['id'] = self.counter = self.counter + 1
        self.todos.append(todo)

        cursor = db.cursor()
        ins_query = "insert into Tasks values(%d, '%s', '%s', '%s')" %(todo['id'], todo['task'], todo['due_by'], todo['status'])
        print(ins_query)
        try:
            cursor.execute(ins_query)
            db.commit()
        except Exception as e:
            print("Error in create task")
            db.rollback()
        return todo

    def update(self, id, data):
        todo = self.get(id)
        todo.update(data)
        print(data)
        upd_query = "update Tasks set task='%s', due_by='%s', status='%s' where id=%d" %(data['task'], data['due_by'], data['status'], id)
        cursor = db.cursor()
        try:
            cursor.execute(upd_query)
            db.commit()
        except Exception as e:
            print("Error in update task")
            db.rollback()
        return todo

    def delete(self, id):
        todo = self.get(id)
        del_query = "delete from Tasks where id=%d" %(id)
        cursor = db.cursor()
        try:
            cursor.execute(del_query)
            db.commit()
        except Exception as e:
            print("Error in delete task")
            db.rollback()
        self.todos.remove(todo)

    def change(self, id, data):
        todo = self.get(id)
        todo.update(data)
        print(data)
        chs_query = "update Tasks set status='%s' where id=%d" %(data['status'], id)
        cursor = db.cursor()
        try:
            cursor.execute(chs_query)
            db.commit()
        except Exception as e:
            print("Error in change task status")
            db.rollback()
        return todo


DAO = TodoDAO()
DAO.create({'task': 'Build an API', 'due_by':'2021-05-20', 'status':'not started'})
DAO.create({'task': '?????', 'due_by':'2021-05-18', 'status':'finished'})
DAO.create({'task': 'profit!', 'due_by':'2021-05-20', 'status':'in progress'})


@ns.route('/')
class TodoList(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''
    @ns.doc('list_todos')
    @ns.marshal_list_with(todo)
    def get(self):
        '''List all tasks'''
        return DAO.todos

    @ns.doc('create_todo')
    @ns.expect(todo)
    @ns.marshal_with(todo, code=201)
    @api.doc(security='apikey')
    @token_required
    def post(self):
        '''Create a new task'''
        return DAO.create(api.payload), 201


@ns.route('/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class Todo(Resource):
    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    def get(self, id):
        '''Fetch a given resource'''
        return DAO.get(id)

    @ns.doc('delete_todo')
    @ns.response(204, 'Todo deleted')
    @api.doc(security='apikey')
    @token_required
    def delete(self, id):
        '''Delete a task given its identifier'''
        DAO.delete(id)
        return '', 204

    @ns.expect(todo)
    @ns.marshal_with(todo)
    @api.doc(security='apikey')
    @token_required
    def put(self, id):
        '''Update a task given its identifier'''
        return DAO.update(id, api.payload)

@ns.route('/status/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class TodoStatus(Resource):
    @ns.expect(status)
    @ns.marshal_with(status)
    @api.doc(security='apikey')
    @token_required
    def put(self, id):
        '''Change a task's status given its identifier'''
        return DAO.change(id, api.payload)


@ns.route('/due')
@ns.response(404, 'Todo not found')
# @ns.param('date', 'Due date of task')
class TodoDate(Resource):
    def get(self):
        '''List all tasks due on specified date'''
        parser = reqparse.RequestParser()
        parser.add_argument('due_date', help='Due date of task')
        args = parser.parse_args()
        print(args)
        return DAO.getDate(args['due_date'])

@ns.route('/overdue')
@ns.response(404, 'Todo not found')
class TodoOverDate(Resource):
    def get(self):
        '''List all tasks overdue today'''
        return DAO.getoverDate()

@ns.route('/finished')
@ns.response(404, 'Todo not found')
class TodoOverDate(Resource):
    def get(self):
        '''List all tasks finished'''
        return DAO.getFinished()

if __name__ == '__main__':
    app.run(debug=True)