Write-Host "🏛️  === ELIGENDO MUNICIPAL QUERY DEMONSTRATION ===" -ForegroundColor Green
Write-Host ""

# Add Node.js to PATH
$env:PATH += ";C:\Users\ficcadv2\node-js"

$municipalDataPath = "data\municipal-election-data.json"

if (Test-Path $municipalDataPath) {
    Write-Host "✅ Loading municipal election data..." -ForegroundColor Green
    $data = Get-Content $municipalDataPath | ConvertFrom-Json
    
    Write-Host "📊 Election: $($data.electionId)" -ForegroundColor Cyan
    Write-Host "📅 Date: $($data.electionDate)" -ForegroundColor Cyan
    Write-Host "🏛️  Type: $($data.electionType)" -ForegroundColor Cyan
    Write-Host ""
    
    # Function to query municipality
    function Query-Municipality {
        param(
            [string]$MunicipalityName,
            [string]$Date = "2024-06-08"
        )
        
        Write-Host "🔍 Querying: $MunicipalityName on $Date" -ForegroundColor Yellow
        
        $municipality = $data.municipalities | Where-Object { 
            $_.municipalityName -eq $MunicipalityName -or 
            $_.municipalityName -like "*$MunicipalityName*" 
        }
        
        if (-not $municipality) {
            Write-Host "❌ Municipality '$MunicipalityName' not found" -ForegroundColor Red
            Write-Host "📍 Available municipalities:" -ForegroundColor Yellow
            foreach ($muni in $data.municipalities) {
                Write-Host "  • $($muni.municipalityName) ($($muni.province), $($muni.region))" -ForegroundColor White
            }
            return
        }
        
        Write-Host ""
        Write-Host "🏛️  === $($municipality.municipalityName.ToUpper()) ELECTION RESULTS ===" -ForegroundColor Green
        Write-Host "📍 Location: $($municipality.province), $($municipality.region)" -ForegroundColor Cyan
        Write-Host "👥 Total Voters: $($municipality.totalVoters.ToString('N0'))" -ForegroundColor Cyan
        Write-Host "🗳️  Total Votes: $($municipality.totalVotes.ToString('N0'))" -ForegroundColor Cyan
        Write-Host "📈 Turnout: $($municipality.turnout.ToString('F1'))%" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "🎯 PARTY RESULTS:" -ForegroundColor Yellow
        
        $sortedParties = $municipality.parties | Sort-Object votes -Descending
        
        for ($i = 0; $i -lt $sortedParties.Count; $i++) {
            $party = $sortedParties[$i]
            $position = $i + 1
            $medal = switch ($position) {
                1 { "🥇" }
                2 { "🥈" }
                3 { "🥉" }
                default { "  " }
            }
            
            Write-Host "$medal $position. $($party.partyName)" -ForegroundColor White
            Write-Host "     🗳️  Votes: $($party.votes.ToString('N0')) ($($party.percentage.ToString('F1'))%)" -ForegroundColor Gray
            
            if ($party.candidates -and $party.candidates.Count -gt 0) {
                Write-Host "     👤 Candidates:" -ForegroundColor Gray
                foreach ($candidate in $party.candidates) {
                    Write-Host "        • $($candidate.candidateName): $($candidate.votes.ToString('N0')) votes" -ForegroundColor DarkGray
                }
            }
        }
        Write-Host ""
    }
    
    # Function to show available municipalities
    function Show-AvailableMunicipalities {
        Write-Host "📍 Available Municipalities:" -ForegroundColor Yellow
        foreach ($muni in $data.municipalities) {
            Write-Host "  • $($muni.municipalityName) ($($muni.province), $($muni.region))" -ForegroundColor White
        }
        Write-Host ""
    }
    
    # Function to get winning party
    function Get-WinningParty {
        param([string]$MunicipalityName)
        
        $municipality = $data.municipalities | Where-Object { 
            $_.municipalityName -eq $MunicipalityName 
        }
        
        if ($municipality) {
            $winner = $municipality.parties | Sort-Object votes -Descending | Select-Object -First 1
            $runnerUp = $municipality.parties | Sort-Object votes -Descending | Select-Object -Skip 1 -First 1
            $margin = if ($runnerUp) { $winner.votes - $runnerUp.votes } else { 0 }
            
            Write-Host "🏆 Winner in $($municipality.municipalityName): $($winner.partyName)" -ForegroundColor Green
            Write-Host "   Votes: $($winner.votes.ToString('N0')) ($($winner.percentage.ToString('F1'))%)" -ForegroundColor Gray
            if ($margin -gt 0) {
                Write-Host "   Margin: $($margin.ToString('N0')) votes" -ForegroundColor Gray
            }
        }
    }
    
    # Parse command line arguments
    if ($args.Count -eq 0) {
        Write-Host "📖 USAGE EXAMPLES:" -ForegroundColor Yellow
        Write-Host "  Query specific municipality:" -ForegroundColor White
        Write-Host "    .\demo-query.ps1 Milano" -ForegroundColor Gray
        Write-Host "    .\demo-query.ps1 Roma" -ForegroundColor Gray
        Write-Host "    .\demo-query.ps1 Napoli" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  Show all available municipalities:" -ForegroundColor White
        Write-Host "    .\demo-query.ps1 --list" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  Show winners for all cities:" -ForegroundColor White
        Write-Host "    .\demo-query.ps1 --winners" -ForegroundColor Gray
        Write-Host ""
        
        Show-AvailableMunicipalities
        
    } elseif ($args[0] -eq "--list") {
        Show-AvailableMunicipalities
        
    } elseif ($args[0] -eq "--winners") {
        Write-Host "🏆 WINNERS BY MUNICIPALITY:" -ForegroundColor Yellow
        foreach ($muni in $data.municipalities) {
            Get-WinningParty $muni.municipalityName
        }
        Write-Host ""
        
    } else {
        $municipalityName = $args[0]
        $date = if ($args.Count -gt 1) { $args[1] } else { "2024-06-08" }
        Query-Municipality -MunicipalityName $municipalityName -Date $date
    }
    
} else {
    Write-Host "❌ Municipal election data file not found: $municipalDataPath" -ForegroundColor Red
    Write-Host "Please run the municipal demo first:" -ForegroundColor Yellow
    Write-Host "  .\run-municipal-demo.ps1" -ForegroundColor Gray
}

Write-Host "Press Enter to exit..." -ForegroundColor Green
Read-Host
