drop schema if exists capstone cascade;
create schema capstone;
set search_path to capstone;

create table card (
    card_id varchar(50) primary key,
    name varchar(50) not null,
    is_funny boolean not null,
    layout varchar(50),
    "text" text,
    print_date date,
    power int not null,
    toughness not null
);

create table card_types(
    card_id varchar(50) foreign key
        references card(card_id),
    sub_types varchar(50),
    types varchar(100),
    super_types varchar(50)
);

create table card_mana(
    card_id varchar(50) foreign key
        references card(card_id),
    color_id varchar(10),
    colors varchar(20),
    cmc int not null,
    mana_cost varchar(20) not null,
    mana_value
);

create table card_price(
    card_id varchar(50) foreign key
        references card(card_id),
    price numeric(8,2) not null,
    "date" date not null,
    printings varchar(100)
);
