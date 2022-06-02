import asyncpg
import json
from datetime import datetime
import pydantic
from aiohttp import web
import gino

from serializer import AdvertisementSerializer


app = web.Application()
db = gino.Gino()


async def init_orm(app):
    # await db.set_bind(f'postgres://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@db/{os.getenv("POSTGRES_DB")}')
    await db.set_bind('postgres://user_aiohttp:12345@127.0.0.1:5432/base_aiohttp')
    await db.gino.create_all()
    yield
    await db.pop_bind().close()


class Advertisement(db.Model):

    __tablename__ = 'advertisement'

    id = db.Column(db.Integer(), primary_key=True)
    user = db.Column(db.String())
    title = db.Column(db.String())
    description = db.Column(db.String(), nullable=False)
    data_create = db.Column(db.DateTime(), server_default=str(datetime.now()))

    __table_args__ = db.UniqueConstraint(user, title)


routes = web.RouteTableDef()
@routes.view('/adv')
@routes.view('/adv/{id}')
class AdvertisementView(web.View):
    async def get(self):
        advertisement_id = self.request.match_info.get('id')
        if advertisement_id is not None:
            advertisement = await Advertisement.get(int(advertisement_id))
            advertisement.data_create = str(advertisement.data_create)

            return web.json_response(advertisement.to_dict())
        else:
            all_advertisement = await db.all(Advertisement.query)
            all_advertisement = [adv.to_dict() for adv in all_advertisement]
            for adv in all_advertisement:
                adv['data_create'] = str(adv['data_create'])

            return web.json_response(all_advertisement)

    async def post(self):
        try:
            advertisement_data = await self.request.json()
        except json.decoder.JSONDecodeError as error:
            return web.json_response({'msg': 'empty data'})

        try:
            advertisement_data_serializer = AdvertisementSerializer(**advertisement_data)
        except pydantic.error_wrappers.ValidationError as error:
            return web.json_response(error.errors())

        advertisement_data = advertisement_data_serializer.dict()
        try:
            new_advertisement = await Advertisement.create(**advertisement_data)
        except asyncpg.exceptions.UniqueViolationError as err:
            return web.json_response({'err': err.args})

        new_advertisement.data_create = str(new_advertisement.data_create)
        return web.json_response(new_advertisement.to_dict())

    async def delete(self):
        advertisement_id = self.request.match_info.get('id')
        if advertisement_id is not None:
            advertisement = await Advertisement.get(int(advertisement_id))
            if advertisement is not None:
                await advertisement.delete()
                return web.json_response({'status': 'OK', 'code': '204'})

        return web.json_response({'status': 'NotFound', 'code': '404'})


app.cleanup_ctx.append(init_orm)
app.add_routes(routes)
web.run_app(app, port=8080)