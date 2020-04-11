import pyfastocloud_models.constants as constants
from flask import request, jsonify, render_template, redirect, url_for
from flask_classy import FlaskView, route
from flask_login import login_required
from pyfastocloud_models.utils.m3u_parser import M3uParser
from pyfastocloud_models.utils.utils import is_valid_http_url

from app.autofill.entry import M3uParseStreams, M3uParseVods
from app.common.service.forms import UploadM3uForm


# routes
class M3uParseStreamsView(FlaskView):
    route_base = '/m3uparse_streams/'

    @login_required
    def show(self):
        m3u = M3uParseStreams.objects.all()
        return render_template('autofill/show_streams.html', m3u=m3u)

    def show_anonim(self):
        m3u = M3uParseStreams.objects.all()
        return render_template('autofill/show_streams_anonim.html', m3u=m3u)

    @route('/search/<sid>', methods=['GET'])
    def search(self, sid):
        line = M3uParseStreams.get_by_id(sid)
        if line:
            return jsonify(status='ok', line=line.to_front_dict()), 200

        return jsonify(status='failed', error='Not found'), 404

    @route('/upload_files', methods=['POST'])
    @login_required
    def upload_files(self):
        form = UploadM3uForm()
        if form.validate_on_submit():
            files = request.files.getlist("files")
            for file in files:
                m3u_parser = M3uParser()
                data = file.read().decode('utf-8')
                m3u_parser.load_content(data)
                m3u_parser.parse()

                for entry in m3u_parser.files:
                    title = entry['title']
                    if len(title) > constants.MAX_STREAM_NAME_LENGTH:
                        continue

                    line = M3uParseStreams.get_by_name(name=title)
                    if not line:
                        line = M3uParseStreams(name=title)

                    tvg_id = entry['tvg-id']
                    if len(tvg_id) and len(tvg_id) < constants.MAX_STREAM_TVG_ID_LENGTH:
                        line.tvg_id.append(tvg_id)

                    tvg_group = entry['tvg-group']
                    if len(tvg_group) and len(tvg_group) < constants.MAX_STREAM_GROUP_TITLE_LENGTH:
                        line.group.append(tvg_group)

                    tvg_logo = entry['tvg-logo']
                    if len(tvg_logo) and len(tvg_logo) < constants.MAX_URI_LENGTH:
                        if is_valid_http_url(tvg_logo, timeout=0.1):
                            line.tvg_logo.append(tvg_logo)

                    line.save()

        return redirect(url_for('M3uParseStreamsView:show'))

    @login_required
    @route('/upload_m3u', methods=['POST', 'GET'])
    def upload_m3u(self):
        form = UploadM3uForm()
        return render_template('autofill/upload_m3u_streams.html', form=form)


# routes
class M3uParseVodsView(FlaskView):
    route_base = '/m3uparse_vods/'

    @login_required
    def show(self):
        m3u = M3uParseVods.objects.all()
        return render_template('autofill/show_vods.html', m3u=m3u)

    def show_anonim(self):
        m3u = M3uParseVods.objects.all()
        return render_template('autofill/show_vods_anonim.html', m3u=m3u)

    @route('/search/<sid>', methods=['GET'])
    def search(self, sid):
        line = M3uParseVods.get_by_id(sid)
        if line:
            return jsonify(status='ok', line=line.to_front_dict()), 200

        return jsonify(status='failed', error='Not found'), 404

    @route('/upload_files', methods=['POST'])
    @login_required
    def upload_files(self):
        form = UploadM3uForm()
        if form.validate_on_submit():
            files = request.files.getlist("files")
            for file in files:
                m3u_parser = M3uParser()
                data = file.read().decode('utf-8')
                m3u_parser.load_content(data)
                m3u_parser.parse()

                for entry in m3u_parser.files:
                    title = entry['title']
                    if len(title) > constants.MAX_STREAM_NAME_LENGTH:
                        continue

                    line = M3uParseVods.get_by_name(title)
                    if not line:
                        line = M3uParseVods(name=title)

                    tvg_group = entry['tvg-group']
                    if len(tvg_group) and len(tvg_group) < constants.MAX_STREAM_GROUP_TITLE_LENGTH:
                        line.group.append(tvg_group)

                    tvg_logo = entry['tvg-logo']
                    if len(tvg_logo) and len(tvg_logo) < constants.MAX_URI_LENGTH:
                        if is_valid_http_url(tvg_logo, timeout=0.1):
                            line.tvg_logo.append(tvg_logo)

                    line.save()

        return redirect(url_for('M3uParseVodsView:show'))

    @login_required
    @route('/upload_m3u', methods=['POST', 'GET'])
    def upload_m3u(self):
        form = UploadM3uForm()
        return render_template('autofill/upload_m3u_vods.html', form=form)
