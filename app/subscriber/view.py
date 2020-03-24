from bson.objectid import ObjectId
from flask import render_template, request, jsonify
from flask_classy import FlaskView, route
from flask_login import login_required
from pyfastocloud_models.service.entry import ServiceSettings
from pyfastocloud_models.subscriber.login.entry import SubscriberUser

from app.common.subscriber.forms import SignUpForm


# routes
class SubscriberView(FlaskView):
    route_base = "/subscriber/"

    @login_required
    def show(self):
        return render_template('subscriber/show.html', subscribers=SubscriberUser.objects.all())

    @login_required
    @route('/add', methods=['GET', 'POST'])
    def add(self):
        form = SignUpForm()
        if request.method == 'POST' and form.validate_on_submit():
            new_entry = form.make_entry()
            new_entry.servers = ServiceSettings.objects.all()
            new_entry.save()
            return jsonify(status='ok'), 200

        return render_template('subscriber/add.html', form=form)

    @login_required
    @route('/edit/<sid>', methods=['GET', 'POST'])
    def edit(self, sid):
        subscriber = SubscriberUser.get_by_id(ObjectId(sid))
        form = SignUpForm(obj=subscriber)
        if request.method == 'POST' and form.validate_on_submit():
            subscriber = form.update_entry(subscriber)
            subscriber.save()
            return jsonify(status='ok'), 200

        return render_template('subscriber/edit.html', form=form)

    @login_required
    @route('/wedit/<sid>', methods=['GET', 'POST'])
    def wedit(self, sid):
        subscriber = SubscriberUser.get_by_id(ObjectId(sid))
        form = SignUpForm(obj=subscriber)
        if request.method == 'POST':
            old_password = subscriber.password
            form.validate_password(False)
            if form.validate_on_submit():
                subscriber = form.update_entry(subscriber)
                subscriber.password = old_password
                subscriber.save()
                return jsonify(status='ok'), 200

        return render_template('subscriber/wedit.html', form=form)

    @login_required
    @route('/remove', methods=['POST'])
    def remove(self):
        data = request.get_json()
        sid = data['sid']
        subscriber = SubscriberUser.get_by_id(ObjectId(sid))
        if subscriber:
            subscriber.delete()
            return jsonify(status='ok'), 200

        return jsonify(status='failed'), 404
