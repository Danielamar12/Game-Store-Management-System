import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.admin import Admin
from app.utils.validators import validate_username, validate_password

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    db.create_all()
    click.echo('Initialized the database.')

@click.command('create-admin')
@click.argument('username')
@click.argument('password')
@with_appcontext
def create_admin_command(username, password):
    """Create an admin user."""
    # Validate username
    valid_username, username_msg = validate_username(username)
    if not valid_username:
        click.echo(f'Error: {username_msg}')
        return

    # Validate password
    valid_password, password_msg = validate_password(password)
    if not valid_password:
        click.echo(f'Error: {password_msg}')
        return

    # Check if username already exists
    if Admin.query.filter_by(username=username).first():
        click.echo('Error: Username already exists')
        return

    admin = Admin(username=username)
    admin.set_password(password)
    
    try:
        db.session.add(admin)
        db.session.commit()
        click.echo(f'Created admin user: {username}')
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error creating admin user: {str(e)}') 