#!/bin/bash
echo "DESTROYING ALL AWS RESOURCES"
echo "This will delete:"
echo "  - All Lambda functions"
echo "  - All API Gateways"
echo "  - All DynamoDB tables"
echo ""
read -p "Are you sure? Type 'DELETE' to confirm: " confirm

if [ "$confirm" = "DELETE" ]; then
  echo "Deleting Lambda functions..."
  for func in $(aws lambda list-functions --query 'Functions[*].FunctionName' --output text); do
    aws lambda delete-function --function-name $func
    echo "  ✓ Deleted: $func"
  done

  echo "Deleting API Gateways..."
  for api in $(aws apigateway get-rest-apis --query 'items[*].id' --output text); do
    aws apigateway delete-rest-api --rest-api-id $api
    echo "  ✓ Deleted API: $api"
  done

  echo "Deleting DynamoDB tables..."
  for table in $(aws dynamodb list-tables --query 'TableNames[*]' --output text); do
    aws dynamodb delete-table --table-name $table
    echo "  ✓ Deleted table: $table"
  done

  echo ""
  echo "All resources deleted. Billing should stop within minutes."
else
  echo "Cancelled. No resources deleted."
fi

read -p "Press Enter to close..."