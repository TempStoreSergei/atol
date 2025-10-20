# подключение роутеров
routers = list()
routers.append(RouterFactory(
    prefix='/api/v1/transactions',
    tags=['Транзакции'],
    routes=TRANSACTIONS_ROUTES,
))
for router in routers:
    app.include(router)


# описание маршрутов
FINES_ROUTES = [
    RouteDTO(
        path="/add_fine",
        endpoint=add_fine,
        response_model=AddFineResponseDTO,
        methods=["POST"],
        status_code=status.HTTP_201_CREATED,
        summary="",
        description="",
        responses={
            status.HTTP_201_CREATED: {
                "description": "",
            },
        },
    ),
]


# описание эндпоинтов
async def add_fine(
    fine_data: AddFineRequestDTO,
    fine_repo: FineDatabaseRepository = Depends(get_fine_repo),
):
    fine  = await fine_repo.create(
        name=fine_data.name,
        price=fine_data.price,
        type=fine_data.type,
    )
    return AddFineResponseDTO(id=fine.id, detail='Штраф добавлена успешно')
