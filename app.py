from dash import Dash, html, dcc
#import dash_core_components as dcc
#import dash_html_components as html
import plotly.express as px
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import numpy as np
import plotly.graph_objects as go
from dotenv import load_dotenv
import os 
import dash_auth
import time

load_dotenv()
cursors=[]
trans=[]

def get_alldata():
    time.sleep(0.1)
    url= 'https://partners.shopify.com/2164727/api/2023-01/graphql.json'
    headers={ 
        'X-Shopify-Access-Token': os.getenv("HEY_TOKEN"), 
        'Content-Type': 'application/json'
      }
    body2="""
    {
        app(id: "gid://partners/App/5865267") {
          events(
            types: [RELATIONSHIP_INSTALLED, RELATIONSHIP_UNINSTALLED, RELATIONSHIP_DEACTIVATED, SUBSCRIPTION_CHARGE_ACCEPTED, SUBSCRIPTION_CHARGE_ACTIVATED, SUBSCRIPTION_CHARGE_CANCELED, SUBSCRIPTION_CHARGE_DECLINED, SUBSCRIPTION_CHARGE_FROZEN, 
            SUBSCRIPTION_CHARGE_UNFROZEN], after:"%s" , first: 100
          )  { 
              pageInfo {
              hasNextPage
            }
            edges {
              cursor
              node {
                occurredAt
                __typename
                ... on RelationshipUninstalled {
                  reason
                  description
    
                  shop {
                    
                    id
                    myshopifyDomain
                    name
                  }
                }
                ... on RelationshipInstalled {
    
                  shop {
                    
                    id
                    myshopifyDomain
                    name
                  }
                }
                ... on RelationshipDeactivated {
    
                  shop {
                    
                    id
                    myshopifyDomain
                    name
                  }
                }
                ... on RelationshipReactivated {
    
                  shop {
                    
                    id
                    myshopifyDomain
                    name
                  }
                }
                ... on SubscriptionChargeAccepted {
    
                  charge {
                    amount {
                      currencyCode
                      amount
                    }
                    billingOn
                    id
                    name
                    test
                  }
                  shop {
                    
                    id
                    myshopifyDomain
                    name
                  }
                }
                ... on SubscriptionChargeActivated {
    
                  charge {
                    amount {
                      currencyCode
                      amount
                    }
                    billingOn
                    id
                    name
                    test
                  }
                  shop {
                    
                    id
                    myshopifyDomain
                    name
                  }
                }
                ... on SubscriptionChargeCanceled {
    
                  charge {
                    amount {
                      currencyCode
                      amount
                    }
                    billingOn
                    id
                    name
                    test
                  }
                  shop {
                    
                    id
                    myshopifyDomain
                    name
                  }
                }
                ... on SubscriptionChargeDeclined {
    
                  charge {
                    amount {
                      currencyCode
                      amount
                    }
                    billingOn
                    id
                    name
                    test
                  }
                  shop {
                    
                    id
                    myshopifyDomain
                    name
                  }
                }
                ... on SubscriptionChargeFrozen {
    
                  charge {
                    amount {
                      currencyCode
                      amount
                    }
                    billingOn
                    id
                    name
                    test
                  }
                  shop {
                    
                    id
                    myshopifyDomain
                    name
                  }
                }
                ... on SubscriptionChargeUnfrozen {
    
                  charge {
                    amount {
                      currencyCode
                      amount
                    }
                    billingOn
                    id
                    name
                    test
                  }
                  shop {
                    
                    id
                    myshopifyDomain
                    name
                  }
                }
              }
            }
          }
              
        }
      }
    """% (cursors[-1] if len(cursors)>0 else "")
    r = requests.post(url=url,headers=headers,json={"query": body2})
    res = r.json()
    response = res['data']['app']['events']['edges']
    for i in response:
        trans.append(i['node'])
        cursors.append(i['cursor'])
    if res['data']['app']['events']['pageInfo']['hasNextPage']==False:
        return 
    else:
        get_alldata()

get_alldata()

VALID_USERNAME_PASSWORD_PAIRS = {
    os.getenv("USER_NAME"): os.getenv("PASSWORD")
}

app = Dash(__name__)
server = app.server
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)  
now=datetime.now()     
transactions=[]
for i in trans:
    if (i['__typename']=="SubscriptionChargeActivated"):        
            transactions.append({'id':i['shop']['id'],'type': i['__typename'],'date':i['occurredAt'],'fee':i['charge']['amount']['amount']})
    else:
        transactions.append({'id':i['shop']['id'],'type': i['__typename'],'date':i['occurredAt'],'fee':''})
    
dff = pd.DataFrame(transactions)
dff['date']=dff['date'].apply(lambda x:datetime.strptime(x,'%Y-%m-%dT%H:%M:%S.%fZ'))
    # dff=dff.sort_values(by=['id','date'],ascending=False)
    
ids=dff.id.unique()
    
    
accepted=dff[ dff['type']=='SubscriptionChargeActivated'].sort_values(by=['date']).drop_duplicates(subset=['id'], keep='first')
cancelled=dff[ dff['type']=='SubscriptionChargeCanceled'].sort_values(by=['date']).drop_duplicates(subset=['id'], keep='first')
frozen=dff[ dff['type']=='SubscriptionChargeFrozen'].sort_values(by=['date']).drop_duplicates(subset=['id'], keep='first')
unfrozen=dff[ dff['type']=='SubscriptionChargeUnfrozen'].sort_values(by=['date']).drop_duplicates(subset=['id'], keep='first')
declined=dff[ dff['type']=='SubscriptionChargeDeclined'].sort_values(by=['date']).drop_duplicates(subset=['id'], keep='first')
    
    
    
    # active paying customers - frozen unfrozen detayi da eklensin.
accepted_no_trial=accepted[accepted['date']+timedelta(days=7)<now] #hala trial surecinde olanlar cikarildi
paying_customers=accepted_no_trial.merge(cancelled, how='left',on='id',indicator=True)
paying_customers2=paying_customers[paying_customers['_merge']=='left_only'] #trial surecinde iptal edenler cikarildi
paying_customers2['fee_x']=paying_customers2['fee_x'].apply(lambda x:float(x))
vis_pay_cus=paying_customers2.set_index('date_x')
vis_pay_cus=vis_pay_cus.resample('M').sum()
vis_pay_cus['cum']=vis_pay_cus.fee_x.cumsum()
vis_pay_cus=vis_pay_cus.reset_index()
    
    # churn - aktif iken iptal etmisler listesi
churn=paying_customers[paying_customers['date_y']-paying_customers['date_x']>timedelta(days=7)]
churn['fee_x']=churn['fee_x'].apply(lambda x:float(x))
churn=churn.set_index('date_y')
churn=churn.resample('M').sum()
churn['fee_x']=churn['fee_x'].apply(lambda x:-1*x)
churn=churn.reset_index()
    
    
    # trial'da iptal etmisler listesi
trial=paying_customers[paying_customers['date_y']-paying_customers['date_x']<timedelta(days=7)]
trial['fee_x']=trial['fee_x'].apply(lambda x:float(x))
trial=trial.set_index('date_y')
trial=trial.resample('M').sum()
trial['fee_x']=trial['fee_x'].apply(lambda x:-1*x)
trial=trial.reset_index()
    
    # decline listesi - odemeyi reddedenler
    
    
    
fig = go.Figure(data=[
        go.Bar(name='Monthly MRR', x=vis_pay_cus['date_x'],y=vis_pay_cus['cum']),
        go.Bar(name='Churn', x=churn['date_y'],y=churn['fee_x']),
        go.Line(name='New Paying Customers',  x=vis_pay_cus['date_x'], y=vis_pay_cus['fee_x']),
        go.Line(name='Trial Cancelled',  x=trial['date_y'], y=trial['fee_x'],marker_color='lightslategrey')
    ])
    # fig.update_layout(plot_bgcolor='red')
       
app.layout = html.Div(children=[
        html.Div(children=[
            html.H1(children='Hey Low Stock Counter Dashboard!',style={'display':'block','font-family': 'sans-serif','margin-top':'60px'})],style={'display': 'flex','align-items': 'center','justify-content': 'center'}),
    
        dcc.Graph(
            id='example-graph',
            figure=fig,
            style={'width': '80vw', 'margin': 'auto'}
        )
    ])                                           
if __name__ == '__main__':
    app.run_server(debug=True)