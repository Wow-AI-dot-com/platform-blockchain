from pydantic import BaseModel, Json
from typing import Optional, List
from datetime import datetime
from typing import List
from utils import RentStatus

class Wallet(BaseModel):
    userId: str
    walletAddress: str
    privateKey: str
    balance: str = '0'
    pendingBalance: str = '0'
    hasApproved: bool = False
    createdAt: datetime = datetime.now()
    updatedAt: datetime = datetime.now()
    lastDeposited: datetime = None
    def update(self, **kwargs):
        for field, value in kwargs.items():
            setattr(self, field, value)
        self.updatedAt = datetime.now()

class Transaction(BaseModel):
    fromAddress: str
    toAddress: str
    transactionHash: str
    tokenAddress: str
    name: str
    amount: str
    blockNumber: str
    createdAt: datetime = datetime.now()
    updatedAt: datetime = datetime.now()
    def update(self, **kwargs):
        for field, value in kwargs.items():
            setattr(self, field, value)
        self.updatedAt = datetime.now()
    
class TransferRequestOnRamp(BaseModel):
    userId: str
    type: str
    fromAddress: str
    toAddress: str
    transactionHash: str
    tokenAddress: str 
    amount: str
    status: str
    createdAt: datetime = datetime.now()
    updatedAt: datetime = datetime.now()
    def update(self, **kwargs):
        for field, value in kwargs.items():
            setattr(self, field, value)
        self.updatedAt = datetime.now()
    
    
class TransferRequestOffRamp(BaseModel):
    userId: str
    type: str
    country: str
    email: str
    tokenAddress: str 
    amount: str
    status: str
    createdAt: datetime = datetime.now()
    updatedAt: datetime = datetime.now()
    def update(self, **kwargs):
        for field, value in kwargs.items():
            setattr(self, field, value)
        self.updatedAt = datetime.now()


class Rent(BaseModel):
    builderAddress: str
    providerAddress: str
    ipfsHash: str
    rentId: str
    isProcess: bool = False
    depositAmountAxB: str
    rateDollarPerHour: str
    totalHoursEstimate: str
    axbPaidPerSecond: str
    totalHoursUse: str = '0'
    paidAmount: Optional[str] = '0'
    transactionHash: Optional[str] = None
    transactionHashCompleted: Optional[str] = None
    transactionHashError: Optional[str] = None
    reasonError: Optional[str] = None
    errorMessage: Optional[str] = None
    endedAt: str = None
    startedAt: str
    status: str = RentStatus.PENDING.value
    fee: Json = {}
    lastPaid: List[int] = []
    createdAt: datetime = datetime.now()
    updatedAt: datetime = datetime.now()
        
class Token(BaseModel):
    address: str
    name: str
    symbol: str
    decimal: int
    amountPerDollar: str
    priceInDollar: str
    createdAt: datetime = datetime.now()
    updatedAt: datetime = datetime.now()
    
class Fee(BaseModel):
    name: str
    gasFeeInDollar: str
    gasFeeInAxB: str
    gasFeeInBNB: str
    createdAt: datetime = datetime.now()
    updatedAt: datetime = datetime.now()
    