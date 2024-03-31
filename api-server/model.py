from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from typing import List

class Wallet(BaseModel):
    userId: str
    walletAddress: str
    privateKey: str
    balance: str = '0'
    pendingBalance: str = '0'
    role: str = 'Builder'
    hasApproved: bool = False
    createdAt: datetime = datetime.now()
    updatedAt: datetime = datetime.now()
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
    dataURL: str
    rentId: str
    depositAmount: str
    ratePerHour: str
    totalHoursDeposit: str
    totalHoursUse: str = '0'
    payAmount: Optional[str] = None
    transactionHash: Optional[str] = None
    transactionHashCompleted: Optional[str] = None
    transactionHashError: Optional[str] = None
    endedAt: Optional[datetime] = None
    isCompleted: bool = False
    isErrored: bool = False
    isSubmitted: bool = False
    createdAt: datetime = datetime.now()
    updatedAt: datetime = datetime.now()
    def update(self, **kwargs):
        for field, value in kwargs.items():
            setattr(self, field, value)
        self.updatedAt = datetime.now()
        
class Token(BaseModel):
    address: str
    name: str
    symbol: str
    decimal: int
    amountPerDollar: str
    createdAt: datetime = datetime.now()
    updatedAt: datetime = datetime.now()
    