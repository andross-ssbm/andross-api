"""added seasons

Revision ID: a661545b59dd
Revises: 
Create Date: 2023-07-14 14:05:45.703022

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a661545b59dd'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('seasons',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('start_date', sa.DateTime(), nullable=False),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    trigger= '''
        CREATE OR REPLACE FUNCTION update_other_seasons()
        RETURNS TRIGGER AS $$
        BEGIN
        IF NEW.is_current = true THEN
        UPDATE seasons
        SET is_current = false
        WHERE is_current = true
        AND id <> NEW.id;
        END IF;

        RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER update_seasons_trigger
        AFTER INSERT ON seasons
        FOR EACH ROW
        EXECUTE FUNCTION update_other_seasons();
    '''
    # ### end Alembic commands ###
    op.execute(trigger)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('seasons')
    # ### end Alembic commands ###
