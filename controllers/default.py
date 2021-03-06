# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----

def index():
    redirect(URL('home'))
    return locals()

def parseHashtags(cheepBody,cid):
    ctr = 0
    if "#" in cheepBody:
        for h in cheepBody.split("#"):
            if ctr > 0:
                print h.split()[0]
                db['hashtags'].insert(**{'hashtag': h.split()[0] , 'cheep_id': cid})
            ctr+=1

@auth.requires_login()
def home():
    db.cheeps.author.default = auth.user
    db.cheeps.tstamp.default = request.now
    db.cheeps.orig_author.default = auth.user
    form = SQLFORM(db.cheeps)
    form.element('textarea[name=body]')['_style'] = 'width:400px; height:40px;'
    form.element('textarea[name=body]')['_placeholder'] = "What's up, lil bird?"
    form2 = SQLFORM(db.cheeps, col3={'name': 'Your full name'})
    form2.element('textarea[name=body]')['_style'] = 'width:400px;height:40px;'
    form2.element('textarea[name=body]')['_placeholder'] = "What's up, lil bird?"
    print request.vars
    if form.process().accepted:
        cheepBody = request.vars.body
        parseHashtags(cheepBody,form.vars.id)

    followees = db(db.followers.follower==auth.user_id)
    list = [auth.user_id] + [row.followee for row in followees.select(db.followers.followee)]
    cheeps = db((db.cheeps.author.belongs(list)) & (db.cheeps.isReply==False)).select(orderby=~db.cheeps.tstamp, limitby=(0,100))
    replies = db(db.replies).select(orderby=~db.replies.child, limitby=(0,100))
    authID = auth.user.id
    return locals()

def profile():
    user = db.auth_user(request.args(0)) or auth.user
    if not user:
        redirect(URL('home'))
    cheeps = db((db.cheeps.author==user.id) & (db.cheeps.isReply==False)).select(orderby=~db.cheeps.tstamp, limitby=(0,100), cache=(cache.ram, 120), cacheable=True)
    details = db(db.auth_user.id==user.id).select()
    totFollowers = db(db.followers.followee==user.id).count()
    tc = db((db.cheeps.orig_author==user.id) & (db.cheeps.isReply==False)).select()
    totCheeps = db((db.cheeps.author==user.id) & (db.cheeps.isReply==False)).count()
    query1 = (db.followers.followee==user.id)
    query2 = (db.followers.follower==auth.user.id)
    listOfFollowers =  db(query1 & query2).select()
    if len(listOfFollowers)!=0:
        isFollow = True
    else:
        isFollow = False
    return locals()

def cheepPage():
    cheep_id = request.vars['cheep_id']
    query1=(db.replies.parent==cheep_id) #Retrieve replies
    query2=(db.replies.child==db.cheeps.id)
    query3=(db.auth_user.id==db.cheeps.author)
    replies = db(query1 & query2 & query3).select()
    cheep = db(db.cheeps.id==cheep_id).select().first()
    auth_id = auth.user.id
    return locals()

def readNotif():
    a = request.vars['notif_id']
    notifRow = db(db.notifs.id == a).select().first()
    notifRow.update_record(opened=True)

@auth.requires_login()
def reply():
    a = request.post_vars
    id_new = db['cheeps'].insert(**{'body': a.body, 'author': a.author, 'tstamp': request.now, 'isReply': True, 'parentCheep': a.parent, 'orig_author': auth.user.id})
    db['replies'].insert(**{'child': id_new, 'parent': a.parent})
    reply_to = db(db.cheeps.id==a.parent).select(db.cheeps.author).first()
    if int(reply_to.author)!=int(a.author):
        print reply_to.author,a.author,reply_to.author!=a.author, "     Wth!"
        db['notifs'].insert(**{'person': reply_to.author, 'notif_type': 2, 'cheep_id': a.parent, 'follower_id': a.author})
    redirect(URL('home'))
    return locals()

def like():
    a = request.post_vars.cheepId
    cheepRow = db(db.cheeps.id == a).select().first()
    author = cheepRow.author
    if cheepRow.isReply==True:
        parentCheep = cheepRow.parentCheep
    else: parentCheep = cheepRow.id
    l = cheepRow.likes
    likeCheck = db((db.likes.liker == auth.user.id) & (db.likes.liked == a)).count()
    #db['notifs'].insert(**{'person': reply_to.author, 'notif_type': 2, 'cheep_id': a.parent, 'follower_id': a.author})
    if likeCheck == 0:
        cheepRow.update_record(likes=l+1)
        db['likes'].insert(**{'liker': auth.user.id , 'liked': a})
        if author!=auth.user.id:
            db['notifs'].insert(**{'person': author, 'notif_type': 1, 'cheep_id': parentCheep, 'follower_id': auth.user.id})
        return 1
    else:
        cheepRow.update_record(likes=l-1)
        db((db.likes.liker == auth.user.id) & (db.likes.liked == a)).delete()
        db((db.notifs.person == author) & (db.notifs.notif_type == 1) & (db.notifs.cheep_id == parentCheep) & (db.notifs.follower_id == auth.user.id)).delete()
        return -1

def recheep():
    a = request.post_vars.cheepId
    cheepRow = db(db.cheeps.id == a).select().first()
    id_new = db['cheeps'].insert(**{'body': cheepRow.body, 'author': auth.user.id, 'tstamp': request.now, 'orig_author': cheepRow.orig_author})
    if cheepRow.author!=auth.user.id:
        db['notifs'].insert(**{'person': cheepRow.author, 'notif_type': 3, 'cheep_id':cheepRow.id, 'follower_id': auth.user.id})
    parseHashtags(cheepRow.body,id_new)
    return locals()

def deleteCheep():
    a = request.post_vars.cheepId
    db(db.cheeps.id == a).delete()
    return locals()

@auth.requires_login()
def notifs():
    notifList = db((db.notifs.person == auth.user.id) & (db.notifs.opened == False)).select()
    return locals()

@auth.requires_login()
def search():
    #form = SQLFORM.factory(Field('name',requires=IS_NOT_EMPTY()))
    if 'name' in request.vars:
        tokens = request.vars['name'].split()
        query1 = reduce(lambda a,b:a&b,
                       [db.auth_user.first_name.contains(k)|db.auth_user.last_name.contains(k) \
                            for k in tokens])
        query2 = reduce(lambda a,b:a&b,
                       [db.hashtags.hashtag.contains(k) \
                            for k in tokens])
        people = db(query1).select( orderby=db.auth_user.first_name|db.auth_user.last_name)
        hashtags = db(query2).select()
        #,left=db.followers.on(db.followers.followee==db.auth_user.id)
        for person in people:
            print person.id
            print auth.user.id
            listOfFollowers =  db((db.followers.followee==person.id) & (db.followers.follower==auth.user.id)).select()
            if len(listOfFollowers)!=0:
                person['isFollow'] = True
                print "You are following " + person.first_name
            else:
                person['isFollow'] = False
                print "You are not following " + person.first_name
        hashCheep = []
        for hashtag in hashtags:
            hashCheep.append(db(db.cheeps.id == hashtag['cheep_id']).select().first())
    else:
        people = []
        hashCheep = []
    return locals()

@auth.requires_login()
def follow():
    me = auth.user
    if request.env.request_method!='POST': raise HTTP(400)
    if request.args(0) =='follow' and not db.followers(follower=me,followee=request.args(1)):
        # insert a new friendship request
        db.followers.insert(follower=me,followee=request.args(1))
        db['notifs'].insert(**{'person': request.args(1), 'notif_type': 4, 'follower_id': auth.user.id})
    elif request.args(0)=='unfollow':
        # delete a previous friendship request
        db(db.followers.follower==me)(db.followers.followee==request.args(1)).delete()
        db((db.notifs.person == request.args(1)) & (db.notifs.notif_type == 4) & (db.notifs.follower_id == auth.user.id)).delete()

def replies():
    if request.env.request_method!='POST': raise HTTP(400)
    parent = request.vars['parent']
    query1=(db.replies.parent==parent)
    query2=(db.replies.child==db.cheeps.id)
    query3=(db.auth_user.id==db.cheeps.author)
    replies = db(query1 & query2 & query3).select()
    print replies
    for reply in replies:
        print reply.cheeps
    return locals()

# ---- API (example) -----
@auth.requires_login()
def api_get_user_email():
    if not request.env.request_method == 'GET': raise HTTP(403)
    return response.json({'status':'success', 'email':auth.user.email})

# ---- Smart Grid (example) -----
@auth.requires_membership('admin') # can only be accessed by members of admin groupd
def grid():
    response.view = 'generic.html' # use a generic view
    tablename = request.args(0)
    if not tablename in db.tables: raise HTTP(403)
    grid = SQLFORM.smartgrid(db[tablename], args=[tablename], deletable=False, editable=False)
    return dict(grid=grid)

# ---- Embedded wiki (example) ----
def wiki():
    auth.wikimenu() # add the wiki to the menu
    return auth.wiki()

# ---- Action for login/register/etc (required for auth) -----
def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())

# ---- action to server uploaded static content (required) ---
@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)
