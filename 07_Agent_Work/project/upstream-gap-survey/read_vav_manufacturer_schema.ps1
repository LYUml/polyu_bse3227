param([string]$Provider="Microsoft.ACE.OLEDB.12.0",[string]$Database="Master32.pr2",[string]$Tag="ace32")
$ErrorActionPreference="Stop"
$base="C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/manufacturer-vav-boundary-source"
$databasePath=Join-Path $base $Database
$conn=New-Object -ComObject ADODB.Connection
$result=$null
try {
 $conn.Mode=1
 $conn.Open("Provider=$Provider;Data Source=$databasePath;Mode=Read;Persist Security Info=False;")
 $schema=$conn.OpenSchema(20)
 $tables=@()
 while(-not $schema.EOF) {
  if($schema.Fields.Item("TABLE_TYPE").Value -eq "TABLE") {$tables+= $schema.Fields.Item("TABLE_NAME").Value}
  $schema.MoveNext()
 }
 $schema.Close()
 $result=@{ok=$true;provider=$Provider;tables=$tables;mode="Read";database=$Database}
 $conn.Close()
} catch {
 $result=@{ok=$false;provider=$Provider;database=$Database;error_type=$_.Exception.GetType().FullName;message=$_.Exception.Message}
}
$result | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $base ("schema-"+$Tag+".json"))
$result | ConvertTo-Json -Depth 4
