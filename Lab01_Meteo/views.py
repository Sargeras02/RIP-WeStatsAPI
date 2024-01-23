from django.shortcuts import render

def GetStationsData(request):
    return render(request, 'stations_list.html',
              { 'data': {
                  'stations': [
                      { 'name': 'МетеоГис', 'id': 0 },
                      { 'name': 'МосМетео', 'id': 1 },
                      { 'name': 'МетеСтан', 'id': 2 }
                  ]
              }})

def GetStationInfo(request, id):
    return render(request, 'station_detail.html',
              { 'data': {
                  'id': id
              }})


def SearchById(request):
    input_id = request.POST['id']
    return GetStationInfo(request, input_id)
