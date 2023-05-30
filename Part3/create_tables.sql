use aither_crypto;

drop table if exists trading_models;

create table trading_models
(
    model_id									varchar(50) not null unique,
    exchange									varchar(20),
    symbol										varchar(10),
    proc_name_buy								varchar(255),
    target_level_buy							decimal(10,2)	default null,
    enabled										tinyint			default 1,
    primary key (model_id)
);


drop table if exists trading_pools;

create table trading_pools
(
    pool_id					bigint unsigned not null unique,
    exchange				varchar(20),
    symbol					varchar(10),
    total_amount			decimal(10,2),
    is_backtest				tinyint(1) default 0,
    primary key (pool_id)
);

drop table if exists trading_pool_models;

create table trading_pool_models
(
    pool_id					bigint,
    model_id				varchar(50),
    primary key (pool_id, model_id)
);


-- Insert the test model
insert into trading_models (model_id, exchange, symbol, proc_name_buy, target_level_buy)
values ('CB_BTC_AITHERCRYPTO', 'coinbase', 'BTC-USD', 'sp_evaluate_buy_CB_BTC_AITHERCRYPTO', 27525.00);

insert into trading_pools (pool_id, exchange, symbol, total_amount, is_backtest)
values (0, 'coinbase', 'BTC-USD', 10000, 1);

insert into trading_pool_models(pool_id, model_id)
values(0, 'CB_BTC_AITHERCRYPTO');




