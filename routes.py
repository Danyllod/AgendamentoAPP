from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from extensions import db, login_manager
from models import User, Appointment, Doctor, Avaliacao, Filho
from datetime import datetime
from validate_docbr import CPF
from email_validator import validate_email, EmailNotValidError
from functools import wraps
from sqlalchemy import case, func
from collections import defaultdict
from flask_login import current_user, logout_user, login_user, login_required
from llm_agent import responder_mensagem
from db import salvar_mensagem, init_db

def load_routes(app):
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    def validate_cpf(cpf):
        cpf_validator = CPF()
        return cpf_validator.validate(cpf)

    def validate_email_address(email):
        try:
            valid = validate_email(email)
            return True
        except EmailNotValidError as e:
            return False

    def validate_password(password):
        if len(password) < 8:
            return False
        if not any(char.isdigit() for char in password):
            return False
        if not any(char in '!@#$%^&*()' for char in password):
            return False
        return True

    @app.route('/')
    def index():
        return render_template('base.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            full_name = request.form['full_name']
            cpf = request.form['cpf']
            email = request.form['email']
            phone = request.form['phone']
            phone_whatsapp = request.form['phone_whatsapp']
            birth_date = request.form['birth_date']
            address = request.form['address']
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            # Validar se as senhas coincidem
            if password != confirm_password:
                flash('As senhas não coincidem.', 'error')
                return redirect(url_for('register'))

            # Validar CPF
            if not validate_cpf(cpf):
                flash('CPF inválido.', 'error')
                return redirect(url_for('register'))

            # Validar Email
            if not validate_email_address(email):
                flash('Email inválido.', 'error')
                return redirect(url_for('register'))

            # Validar Telefone
            if not phone.isdigit() or len(phone) < 10 or len(phone) > 15:
                flash('Telefone inválido. Deve conter entre 10 e 15 dígitos.', 'error')
                return redirect(url_for('register'))

            # Validar Data de Nascimento
            try:
                birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d')
                today = datetime.today()
                age = today.year - birth_date_obj.year - ((today.month, today.day) < (birth_date_obj.month, birth_date_obj.day))
                if age < 18:
                    flash('Você deve ter pelo menos 18 anos para se cadastrar.', 'error')
                    return redirect(url_for('register'))
            except ValueError:
                flash('Data de nascimento inválida.', 'error')
                return redirect(url_for('register'))

            # Validar Senha
            if not validate_password(password):
                flash('A senha deve ter pelo menos 8 caracteres, incluindo um número e um caractere especial.', 'error')
                return redirect(url_for('register'))

            # Verificar se o CPF já está cadastrado
            if User.query.filter_by(cpf=cpf).first():
                flash('CPF já cadastrado.', 'error')
                return redirect(url_for('register'))

            # Verificar se o Email já está cadastrado
            if User.query.filter_by(email=email).first():
                flash('Email já cadastrado.', 'error')
                return redirect(url_for('register'))

            # Criar novo usuário
            user = User(full_name=full_name, cpf=cpf, email=email, phone=phone, 
                        phone_whatsapp=phone_whatsapp, birth_date=birth_date_obj, address=address)
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            flash('Cadastro realizado com sucesso! Você será redirecionado para a página de login em 3 segundos.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            cpf = request.form['cpf']
            password = request.form['password']
        
            user = User.query.filter_by(cpf=cpf).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('CPF ou senha inválidos.', 'error')
                return redirect(url_for('login'))
        return render_template('login.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html', current_user=current_user)

    @app.route('/agendamento_online')
    @login_required
    def agendamento():
        user = current_user
        if not user:
            flash('Usuário não encontrado. Faça login novamente.', 'error')
            return redirect(url_for('login'))
        return render_template('agendamento.html', current_user=user)
    
    # NOVA ROTA: Painel de Filhos (para agendamento online infanto)
    @app.route('/painel_filhos')
    @login_required
    def painel_filhos():
        # Obtém os filhos do usuário logado (relacionamento definido no modelo User)
        filhos = current_user.filhos
        return render_template('painel_filhos.html', filhos=filhos)
    
    # NOVA ROTA: Cadastro de Filho
    @app.route('/cadastrar_filho', methods=['GET', 'POST'])
    @login_required
    def cadastrar_filho():
        if request.method == 'POST':
            nome_completo = request.form.get('nome_completo')
            nome_pai = request.form.get('nome_pai')
            nome_mae = request.form.get('nome_mae')
            cpf = request.form.get('cpf')
            idade = request.form.get('idade')
            endereco = request.form.get('endereco')
            # Aqui você pode adicionar validações extras (e verificar se o CPF já existe, por exemplo)
            novo_filho = Filho(
                nome_completo=nome_completo,
                nome_pai=nome_pai,
                nome_mae=nome_mae,
                cpf=cpf,
                idade=int(idade),
                endereco=endereco,
                user_id=current_user.id
            )
            db.session.add(novo_filho)
            db.session.commit()
            flash('Filho cadastrado com sucesso!', 'success')
            return redirect(url_for('painel_filhos'))
        return render_template('cadastrar_filho.html')
    
    @app.route('/agendar_consulta_infanto', methods=['GET', 'POST'])
    @login_required
    def agendar_consulta_infanto():
        if request.method == 'POST':
            child_id = request.form.get('child_id')
            specialty = request.form.get('specialty')
            doctor_id = request.form.get('doctor_id')
            appointment_date_str = request.form.get('appointment_date')
            description = request.form.get('description')

            # Obter o nome do filho para incluir na descrição
            filho = db.session.get(Filho, int(child_id))
            nome_filho = filho.nome_completo if filho else "Filho não identificado"

            try:
                appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%dT%H:%M')
                if appointment_date < datetime.now():
                    flash('Não é possível agendar consultas retroativas.', 'error')
                    return redirect(url_for('agendar_consulta_infanto'))

                appointment = Appointment(
                    user_id=current_user.id,
                    doctor_id=doctor_id,
                    appointment_date=appointment_date,
                    appointment_type=specialty,
                    description=f"{description} (Consulta para: {nome_filho})",
                    status='Aguardando Aprovação'
                )
                db.session.add(appointment)
                db.session.commit()
                flash('Consulta agendada para o filho com sucesso!', 'success')
                return redirect(url_for('painel_filhos'))
            except ValueError:
                flash('Data ou horário inválido.', 'error')
                return redirect(url_for('agendar_consulta_infanto'))

        filhos = current_user.filhos
        return render_template('agendar_consulta_infanto.html', filhos=filhos)


    @app.route('/schedule', methods=['POST'])
    @login_required
    def schedule():
        if request.method == 'POST':
            user_id = current_user.id
            specialty = request.form['specialty']
            doctor_id = request.form.get('doctor_id')
            appointment_date_str = request.form['appointment_date']
            description = request.form['description']

            try:
                # Converter a data para o formato correto
                appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%dT%H:%M')
                
                # Validar a data
                if appointment_date < datetime.now():
                    flash('Não é possível agendar consultas retroativas.', 'error')
                    return redirect(url_for('agendamento'))

                # Criar o agendamento
                appointment = Appointment(
                    user_id=current_user.id,
                    doctor_id=doctor_id,
                    appointment_date=appointment_date,
                    appointment_type=specialty,
                    description=description,
                    status='Aguardando Aprovação'
                )

                db.session.add(appointment)
                db.session.commit()

                flash('Consulta agendada com sucesso!', 'success')
                return redirect(url_for('dashboard'))

            except ValueError:
                flash('Data ou horário inválidos.', 'error')
                return redirect(url_for('agendamento'))

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        session.pop('user_id', None)
        flash('Você saiu da sua conta.')
        return redirect(url_for('home'))

    @app.route('/admin')
    @login_required
    def admin_panel():
        user = current_user
        if user.is_admin == 0:
            flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        appointments = Appointment.query.all()
        doctors = Doctor.query.all()
        # Dependendo do nível de admin, renderiza o template desejado
        if user.is_admin == 1:
            return render_template('admin_panel1.html', current_user=user, appointments=appointments, doctors=doctors)
        else:
            return render_template('admin_panel.html', current_user=user, appointments=appointments, doctors=doctors)

    @app.route('/update_status/<int:appointment_id>', methods=['POST'])
    @login_required
    def update_status(appointment_id):
        # Usar current_user para obter informações do usuário autenticado
        if not current_user.is_admin:
            flash('Acesso negado. Você não é um administrador.', 'error')
            return redirect(url_for('dashboard'))

        appointment = Appointment.query.get_or_404(appointment_id)
        new_status = request.form['status']
        appointment.status = new_status
        db.session.commit()

        flash('Status da consulta atualizado com sucesso!', 'success')
        return redirect(url_for('admin_panel'))

    @app.route('/update_appointment/<int:appointment_id>', methods=['POST'])
    @login_required
    def update_appointment(appointment_id):
        if not current_user.is_admin:
            flash('Acesso negado.', 'error')
            return redirect(url_for('dashboard'))

        appointment = Appointment.query.get_or_404(appointment_id)
        appointment.doctor_id = request.form.get('doctor_id')
        appointment.status = request.form.get('status')
        appointment_date_str = request.form['appointment_date']
        appointment.appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%dT%H:%M')

        db.session.commit()
        flash('Consulta atualizada!', 'success')
        return redirect(url_for('admin_panel'))

    @app.route('/edit_user/<int:user_id>')
    @login_required
    def edit_user(user_id):
        if not current_user.is_admin:
            flash('Acesso negado. Você não é um administrador.', 'error')
            return redirect(url_for('dashboard'))

        user = db.session.get(User, user_id)
        return render_template('edit_user.html', user=user)

    @app.route('/update_user/<int:user_id>', methods=['POST'])
    @login_required
    def update_user(user_id):
        if not current_user.is_admin:
            flash('Acesso negado. Você não é um administrador.', 'error')
            return redirect(url_for('dashboard'))

        user = db.session.get(User, user_id)
        user.full_name = request.form['full_name']
        user.cpf = request.form['cpf']
        user.email = request.form['email']
        user.phone = request.form['phone']
        birth_date_str = request.form['birth_date']
        user.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
        user.address = request.form['address']
        user.is_admin = 'is_admin' in request.form

        db.session.commit()
        flash('Dados do usuário atualizados com sucesso!', 'success')
        return redirect(url_for('admin_panel'))

    @app.route('/edit_profile')
    @login_required
    def edit_profile():
        user = current_user
        return render_template('edit_profile.html', current_user=user)

    @app.route('/update_profile', methods=['POST'])
    @login_required
    def update_profile():
        user = current_user
        user.full_name = request.form['full_name']
        user.email = request.form['email']
        user.phone = request.form['phone']
        birth_date_str = request.form['birth_date']
        user.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
        user.address = request.form['address']

        db.session.commit()
        flash('Dados atualizados com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/update_doctor/<int:appointment_id>', methods=['POST'])
    @login_required
    def update_doctor(appointment_id):
        if not current_user.is_admin:
            flash('Acesso negado. Você não é um administrador.', 'error')
            return redirect(url_for('dashboard'))

        appointment = Appointment.query.get_or_404(appointment_id)
        new_doctor = request.form['doctor']
        appointment.doctor = new_doctor

        db.session.commit()
        flash('Médico atualizado com sucesso!', 'success')
        return redirect(url_for('admin_panel'))

    @app.route('/reschedule_or_cancel/<int:appointment_id>', methods=['POST'])
    @login_required
    def reschedule_or_cancel(appointment_id):
        appointment = Appointment.query.get_or_404(appointment_id)
        action = request.form['action']

        if action == 'remarcar':
            flash('Funcionalidade de remarcação em desenvolvimento.', 'info')
        elif action == 'cancelar':
            db.session.delete(appointment)
            db.session.commit()
            flash('Consulta cancelada com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/request_reschedule_or_cancel/<int:appointment_id>', methods=['POST'])
    @login_required
    def request_reschedule_or_cancel(appointment_id):
        appointment = Appointment.query.get_or_404(appointment_id)
        action = request.form['action']

        if action == 'remarcar':
            appointment.status = 'Solicitado Remarcação'
            flash('Solicitação de remarcação enviada para aprovação.', 'info')
        elif action == 'cancelar':
            appointment.status = 'Solicitado Cancelamento'
            flash('Solicitação de cancelamento enviada para aprovação.', 'info')

        db.session.commit()
        return redirect(url_for('dashboard'))

    @app.route('/approve_request/<int:appointment_id>', methods=['POST'])
    @login_required
    def approve_request(appointment_id):
        if not current_user.is_admin:
            flash('Acesso negado. Você não é um administrador.', 'error')
            return redirect(url_for('dashboard'))

        appointment = Appointment.query.get_or_404(appointment_id)
        action = request.form['action']

        if action == 'aprovar':
            if appointment.status == 'Solicitado Remarcação':
                appointment.appointment_date = appointment.new_appointment_date
                appointment.status = 'Consulta Remarcada'
                flash('Remarcação aprovada com sucesso!', 'success')
            elif appointment.status == 'Solicitado Cancelamento':
                appointment.status = 'Consulta Cancelada'
                flash('Cancelamento aprovado com sucesso!', 'success')
        elif action == 'rejeitar':
            appointment.status = 'Consulta Marcada'
            flash('Solicitação rejeitada.', 'warning')

        appointment.new_appointment_date = None
        db.session.commit()
        return redirect(url_for('admin_panel'))

    @app.route('/consultas')
    @login_required
    def consultas():
        user = current_user
        appointments = (
            Appointment.query
            .filter_by(user_id=user.id)
            .order_by(
                case(
                    (Appointment.status == 'Aguardando Aprovação', 1),
                    (Appointment.status == 'Consulta Marcada', 2),
                    (Appointment.status == 'Consulta Remarcada', 3),
                    (Appointment.status == 'Concluído', 4),
                    else_=5
                )
            )
            .all()
        )
        return render_template('consultas.html', appointments=appointments)

    @app.route('/estatisticas')
    @login_required
    def estatisticas():
        appointments = Appointment.query.all()

        stats = {
            "total_appointments": len(appointments),
            "specialties_consulted": set(),
            "doctors_attended": set(),
            "appointments_by_specialty": defaultdict(int),
            "appointments_by_month": defaultdict(int),
        }

        for appointment in appointments:
            stats["specialties_consulted"].add(appointment.appointment_type)
            stats["appointments_by_specialty"][appointment.appointment_type] += 1

            if appointment.doctor:
                stats["doctors_attended"].add(appointment.doctor)

            month_key = appointment.appointment_date.strftime('%Y-%m')
            stats["appointments_by_month"][month_key] += 1

        stats["specialties_consulted"] = len(stats["specialties_consulted"])
        stats["doctors_attended"] = len(stats["doctors_attended"])
        stats["appointments_by_specialty"] = dict(stats["appointments_by_specialty"])
        stats["appointments_by_month"] = dict(stats["appointments_by_month"])

        return render_template('estatisticas.html', stats=stats)

    @app.route('/avalie_nos')
    @login_required
    def avalie_nos():
        medicos = Doctor.query.all()
        return render_template('avalie_nos.html', medicos=medicos)

    @app.route('/enviar_avaliacao', methods=['POST'])
    @login_required
    def enviar_avaliacao():
        try:
            doctor_id = request.form.get('doctor_id')
            qualidade_medico = request.form.get('qualidade_medico')
            comentarios_medico = request.form.get('comentarios_medico')
            recepcao = request.form.get('recepcao')
            recepcionista_nome = request.form.get('recepcionista_nome')
            qualidade_recepcionista = request.form.get('qualidade_recepcionista')
            comentarios_recepcionista = request.form.get('comentarios_recepcionista')

            conn = sqlite3.connect("agendamento.db")
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO avaliacoes
                (user_id, doctor_id, qualidade_medico, comentarios_medico,
                recepcao, recepcionista_nome, qualidade_recepcionista, comentarios_recepcionista)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                current_user.id,
                doctor_id,
                qualidade_medico,
                comentarios_medico,
                recepcao,
                recepcionista_nome,
                qualidade_recepcionista,
                comentarios_recepcionista
            ))
            conn.commit()
            conn.close()

            flash("Avaliação enviada com sucesso!", "success")
            return redirect(url_for('dashboard'))

        except Exception as e:
            print("Erro ao salvar avaliação:", e)
            flash("Erro ao enviar avaliação.", "danger")
            return redirect(url_for('dashboard'))

    @app.route('/cadastrar_medico', methods=['GET', 'POST'])
    @login_required
    def cadastrar_medico():
        if not current_user.is_admin:
            flash('Acesso negado. Área restrita a administradores.', 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            full_name = request.form['full_name']
            name = request.form['name']
            crm = request.form['crm']
            specialty = request.form['specialty']
            schedule = request.form.get('schedule', '')

            if Doctor.query.filter_by(crm=crm).first():
                flash('CRM já cadastrado.', 'error')
                return redirect(url_for('cadastrar_medico'))

            novo_medico = Doctor(
                full_name=full_name,
                name=name,
                crm=crm,
                specialty=specialty
            )
            db.session.add(novo_medico)
            db.session.commit()

            flash('Médico cadastrado com sucesso!', 'success')
            return redirect(url_for('lista_equipe'))

        return render_template('cadastrar_medico.html')

    @app.route('/sucesso')
    def sucesso():
        return "Médico cadastrado com sucesso!"

    @app.route('/lista_medico')
    @login_required
    def lista_equipe():
        if not current_user.is_admin:
            flash('Acesso negado. Área restrita a administradores.', 'error')
            return redirect(url_for('dashboard'))

        medicos = db.session.query(
            Doctor,
            func.count(Appointment.id).label('total_consultas'),
            func.coalesce(func.avg(Avaliacao.satisfaction_score), 0.0).label('media_avaliacao')
        ).outerjoin(Appointment, Doctor.id == Appointment.doctor_id
        ).outerjoin(Avaliacao, Doctor.id == Avaliacao.doctor_id
        ).group_by(Doctor.id).all()

        return render_template('lista_equipe.html', medicos=medicos)

    @app.route('/get-doctors/<specialty>')
    @login_required
    def get_doctors(specialty):
        doctors = Doctor.query.filter_by(specialty=specialty).all()
        return jsonify([{
            'id': doctor.id,
            'name': doctor.name,
            'crm': doctor.crm
        } for doctor in doctors])

    @app.route('/deletar_medico/<int:medico_id>', methods=['POST'])
    @login_required
    def deletar_medico(medico_id):
        if not current_user.is_admin:
            flash('Acesso negado. Área restrita a administradores.', 'error')
            return redirect(url_for('dashboard'))

        medico = Doctor.query.get_or_404(medico_id)

        if medico.appointments or medico.avaliacoes:
            flash('Não é possível excluir o médico pois há consultas ou avaliações associadas.', 'error')
            return redirect(url_for('lista_equipe'))

        db.session.delete(medico)
        db.session.commit()
        flash('Médico excluído com sucesso!', 'success')
        return redirect(url_for('lista_equipe'))
    
    @app.route('/editar_filho/<int:filho_id>', methods=['GET', 'POST'])
    @login_required
    def editar_filho(filho_id):
    # Busca o registro do filho com base no ID
        filho = db.session.get(Filho, filho_id)
        if not filho:
            flash('Filho não encontrado.', 'error')
            return redirect(url_for('painel_filhos'))
    
    # Verifica se o filho pertence ao usuário logado
        if filho.user_id != current_user.id:
            flash('Acesso negado.', 'error')
            return redirect(url_for('painel_filhos'))
    
        if request.method == 'POST':
        # Atualiza os dados do filho com os valores do formulário
            filho.nome_completo = request.form.get('nome_completo')
            filho.nome_pai = request.form.get('nome_pai')
            filho.nome_mae = request.form.get('nome_mae')
            filho.cpf = request.form.get('cpf')
            try:
                filho.idade = int(request.form.get('idade'))
            except (ValueError, TypeError):
                flash('Idade inválida.', 'error')
                return redirect(url_for('editar_filho', filho_id=filho.id))
            filho.endereco = request.form.get('endereco')
            db.session.commit()
            flash('Filho atualizado com sucesso!', 'success')
            return redirect(url_for('painel_filhos'))
    
    # Renderiza o template de edição passando o objeto filho
        return render_template('editar_filho.html', filho=filho)

# Rota para excluir um filho
    @app.route('/excluir_filho/<int:filho_id>', methods=['POST'])
    @login_required
    def excluir_filho(filho_id):
        filho = db.session.get(Filho, filho_id)
        if not filho:
            flash('Filho não encontrado.', 'error')
            return redirect(url_for('painel_filhos'))
        if filho.user_id != current_user.id:
            flash('Acesso negado.', 'error')
            return redirect(url_for('painel_filhos'))
        db.session.delete(filho)
        db.session.commit()
        flash('Filho excluído com sucesso!', 'success')
        return redirect(url_for('painel_filhos'))

    @app.route('/webhook', methods=['POST'])
    def webhook():
        data = request.get_json()
        numero = data.get("numero")
        texto = data.get("mensagem")

        print(f"📩 Mensagem recebida do WhatsApp: {texto}")

        try:
            resposta = responder_mensagem(texto, numero=numero)
            print(f"🤖 Resposta da IA: {resposta}")
        except Exception as e:
            print(f"❌ Erro ao gerar resposta da IA: {e}")
            resposta = "Desculpe, houve um erro ao gerar a resposta."

        salvar_mensagem(numero, texto, resposta)
        return jsonify({"resposta": resposta})
    
    @app.route('/blog')
    def blog():
    # Por enquanto, esta função apenas renderiza uma nova página HTML
        return render_template('blog.html')

    @app.route('/offline.html')
    def offline():
        return render_template('offline.html')
    
    from flask import send_from_directory

    @app.route('/sw.js')
    def sw():
        return send_from_directory('static', 'sw.js')
    
    @app.route('/home')
    def home():
        return render_template('home.html')
