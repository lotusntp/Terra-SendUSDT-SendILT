from distutils.util import execute
from terra_sdk.client.lcd import AsyncLCDClient
from terra_sdk.key.mnemonic import MnemonicKey
from terra_sdk.core import Coins, Coin
from terra_sdk.core.fee import Fee
import json
import time
from datetime import datetime
import asyncio
import threading
from terra_sdk.client.lcd.api.tx import CreateTxOptions
from terra_sdk.core.bank import MsgSend 
from terra_sdk.core.wasm import MsgStoreCode, MsgInstantiateContract, MsgExecuteContract
from colorama import Fore
from colorama import Style


import requests
"""""""""""""""""""""""""""
//PRELOAD
"""""""""""""""""""""""""""


gas_price_dict = requests.get("https://api.terra.dev/gas-prices").json()
gas = float(gas_price_dict['uusd'])*10**6


f = open('./accounts.json',)
dataAccount = json.load(f)
f.close()

f = open('./setting.json',)
setting = json.load(f)
f.close()

terra = AsyncLCDClient("https://lcd.terra.dev", "columbus-5")
mk = MnemonicKey(
            mnemonic=setting['mnemonic_mainwallet'])
wallet = terra.wallet(mk)

def timestamp():
    nowTime = int(datetime.timestamp(datetime.now()))
    timeUnit = datetime.fromtimestamp(nowTime).strftime('%Y-%m-%d %H:%M:%S')
    fomat_dt = f'[{timeUnit}]'
    return fomat_dt


async def addMainAccount():
    try:
        global wallet
        mk = MnemonicKey(
            mnemonic=setting['mnemonic_mainwallet'])
        wallet = terra.wallet(mk)
        print(f'{timestamp()} {Fore.CYAN}Add main account success{Style.RESET_ALL}')
    except:
        print(f"{timestamp()} {Fore.RED}Can't add main account{Style.RESET_ALL}")


async def addSubAccount(name,memoni):
    try:
        
        mk = MnemonicKey(
            mnemonic=memoni)
        wallet = terra.wallet(mk)
        print(f'{timestamp()} {Fore.CYAN}Add sub {name} success{Style.RESET_ALL}')
        return wallet
    except:
        print(f"{timestamp()} {Fore.RED}Can't add main account{Style.RESET_ALL}")


async def getITL(subWallet,name):
    try:
          result = await terra.wasm.contract_query(setting['ILTContract'],{'balance': {"address": subWallet.key.acc_address}})
          ilt = int(result['balance'])
          print(f'{timestamp()} {Fore.CYAN}{name} balance : {Fore.GREEN}{ilt/10**6} ILT{Style.RESET_ALL}')
          return ilt
    except:
        print(f"{timestamp()} {Fore.RED}Can't get balance ILT {name}{Style.RESET_ALL}")


async def execute_contract(sender,execute_msg):
    try:
        execute = MsgExecuteContract(sender=sender.key.acc_address, contract=setting['ILTContract'],execute_msg=execute_msg)
        tx = sender.create_and_sign_tx(options=[execute],fee=Fee(4000000,"1000000uusd"))
        result = await terra.tx.broadcast(tx)
    except Exception as inst:
        print(f"{inst}")

async def sendILT(mainWallet,subWallet,name,amount):
    try:
        
        execute =  MsgExecuteContract(
                    sender=subWallet.key.acc_address,
                    contract="terra1zjhsuvuy5z7ucvx56facefmlrrgluhun27chlf",
                    execute_msg={"transfer": {"recipient": mainWallet.key.acc_address,"amount":str(amount)}}
                )
        
        execute_tx = await subWallet.create_and_sign_tx(
        CreateTxOptions(msgs=[execute])
        )
        result = await terra.tx.broadcast(execute_tx)
        if result.height > 0:
            print(f"{timestamp()} {Fore.YELLOW}Success{Style.RESET_ALL} {Fore.CYAN}{name} send ILT to Main Account{Style.RESET_ALL}")
        elif result.height ==0:
            print(f"{timestamp()} {Fore.RED}Fail {name} send ILT to Main Account{Style.RESET_ALL}")
            print(result.raw_log)
        
        
    except Exception as inst:
        print(f"{inst}")

async def sendUUSD(mainWallet,subWallet,name):
    try:
        
        tx_options = CreateTxOptions(
            msgs=[
                MsgSend(
                    from_address=mainWallet.key.acc_address,
                    to_address=subWallet.key.acc_address,
                    amount=Coins([Coin("uusd", 1000000)])
                )
            ],
            gas="auto",
            gas_prices=Coins(gas_price_dict),
            fee_denoms="uusd",
            gas_adjustment=1.5
        )

        tx = await wallet.create_and_sign_tx(options=tx_options)
        result = await terra.tx.broadcast(tx)
        if result.height > 0:
            print(f"{timestamp()} {Fore.YELLOW}Success{Style.RESET_ALL} {Fore.CYAN}send UUSD to {name}{Style.RESET_ALL}")
        elif result.height ==0:
            print(f"{timestamp()} {Fore.RED}Fail {name} send UUSD to {name}{Style.RESET_ALL}")
            print(result.raw_log)
        
    except:
        print(f"{timestamp()} {Fore.RED}Fail can't send UUSD to {name}{Style.RESET_ALL}")



async def getBalanceUUSDMain(wallet):
    try:
        balance = await terra.bank.balance(wallet)
        coinUSSD =0
        for i in range(len(balance)):
            if i == 0:
                coinZ = balance[i]
                coinSplit = str(coinZ)
                coinArr = coinSplit.split(",")
                coinUSSD = Coin.from_str(coinArr[1])
                print(f'{timestamp()} {Fore.CYAN}Main account balance UUSD: {Fore.GREEN}{coinUSSD.amount/10**6} UUSD{Style.RESET_ALL}')
                
        
        return coinUSSD.amount / 10**6
    except:
        print(f"{timestamp()} {Fore.RED}Can't get balance main account uusd{Style.RESET_ALL}")

async def getBalanceUUSDSub(subAccount,name):
    try:
        balance = await terra.bank.balance(subAccount)
        
        coinUSSD =0
        for i in range(len(balance)):
            if i == 0:
                
                coinZ = balance[i]
                coinSplit = str(coinZ)
                
                coinArr = coinSplit.split(",")
                if len(coinArr) == 1:
                    coinUSSD = Coin.from_str(coinArr[0])
                elif  len(coinArr) == 2:
                    coinUSSD = Coin.from_str(coinArr[1])
                
                print(f'{timestamp()} {Fore.CYAN}{name} balance UUSD: {coinUSSD.amount/10**6} UUSD{Style.RESET_ALL}')
                
        
        return coinUSSD.amount / 10**6
    except:
        print(f"{timestamp()} {Fore.RED}Can't get balance {name} uusd{Style.RESET_ALL}")


async def main():
    
    for key in dataAccount:
        name = key['name']
        memoni = key['memoni']
        balanceMainUUSD = await getBalanceUUSDMain(wallet.key.acc_address)
        
        if balanceMainUUSD >= 2:
            subAccount = await addSubAccount(name,memoni)
            coinILT = await getITL(subAccount,name)
            
            if coinILT > 1000000:
                balanceSubUUSD = await getBalanceUUSDSub(subAccount.key.acc_address,name)
                
                if balanceSubUUSD >= 0.15:
                    
                    await sendILT(wallet,subAccount,name,coinILT)
                else:
                    await sendUUSD(wallet,subAccount,name)
                    balanceSubUUSD = await getBalanceUUSDSub(subAccount.key.acc_address,name)
                    if balanceSubUUSD >= 0.15:
                        await sendILT(wallet,subAccount,name,coinILT)
                    else:
                        await sendUUSD(wallet,subAccount,name)
                        balanceSubUUSD = await getBalanceUUSDSub(subAccount.key.acc_address,name)
                        if balanceSubUUSD >= 0.15:
                            await sendILT(wallet,subAccount,name,coinILT)
        else:
            print(f"{timestamp()} {Fore.RED}Main account don't have UUSD{Style.RESET_ALL}")
    

asyncio.get_event_loop().run_until_complete(main())