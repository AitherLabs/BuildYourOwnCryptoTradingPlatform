use aither_crypto;

drop procedure if exists sp_evaluate_buy_CB_BTC_AITHERCRYPTO;

delimiter $$
create procedure sp_evaluate_buy_CB_BTC_AITHERCRYPTO
(
	locDate				datetime,
    locModelID			varchar(50)
)
this_proc:begin

    declare dLastPrice				decimal(10,2);
    declare dTargetLevelBuy			decimal(10,2);
    declare sExchange 				varchar(20);
    declare sSymbol 				varchar(10);
    
    select 
		m.exchange, m.symbol, m.target_level_buy
        into @sExchange, @sSymbol, @dTargetLevelBuy
	from trading_models m
    where 
		m.model_id=locModelID;
    
    -- Get the last price using the passed in date
	select
		price into @dLastPrice
    from
		price_history
	where
		exchange = @sExchange
			and symbol = @sSymbol
			and created <= locDate
			and created >= date_add(locDate, interval -(1) hour)
	order by created desc
	limit 1;
    
    -- Return any recommendation in a dataset
    select 
		'BUY' as 'action',
		@dLastPrice as 'last_price',
        @dTargetLevelBuy as 'target_price'
	where
		@dLastPrice<@dTargetLevelBuy;
end$$

delimiter ;

-- call sp_evaluate_buy_CB_BTC_AITHERCRYPTO("2023-05-15 18:35:00", "CB_BTC_AITHERCRYPTO");

