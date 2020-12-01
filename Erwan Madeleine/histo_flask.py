from flask import *
import io
import csv
from collections import OrderedDict
from itertools import islice
import json

#to be able to load Tulip
import sys
sys.path.insert(0,'/net/ens/tulip/lib/tulip/python')

from tulip import tlp

#NE PAS MODIFIER LA LIGNE SUIVANTE
app = Flask(__name__)



############## FONCTIONS ##############



def graphe_marvel_sans_comics(g):
    #Cette fonction prend le graphe marvel et renvoie un dictionnaire 
    #Les cles de ce dictionnaire sont les nodes du graphe
    #Les valeurs correspondantes sont la liste des héros à distance 2. 
    
    dico_nodes = {}
    picon = g.getStringProperty("viewIcon")
    for n in g.getNodes():
        if(picon[n]=="md-human"):
            dico_nodes[n] = []
            neigh = g.getInOutNodes(n) 
            # On récupère tous les comics dans lequel le heros apparâit
            for v in neigh : 
                #on récupère tous les heros de ce comic, sauf n 
                #on les met dans la liste d'adj si ils n'y sont pas deja
                v_neigh = g.getInOutNodes(v)
                for u in v_neigh : 
                    # Changer pour mettre un poids à la place
                    if( ( u not in dico_nodes[n] ) and (u != n) ):
                        dico_nodes[n].append(u)

    return dico_nodes

def graphe_heros_sans_comics(g):

    dico_nodes = {}
    picon = g.getStringProperty("viewIcon")
    for n in g.getNodes():
        if(picon[n]=="md-human"): #Normalement on est certain que toutes les nodes sont des personnages
            dico_nodes[n] = []
            neigh = g.getInOutNodes(n) # On récupère tous les heros voisins de n
            for v in neigh :
                if( ( v not in dico_nodes[n] ) and (v != n) ):
                        dico_nodes[n].append(v)
    return dico_nodes


def graphe_marvel_avec_comics(g):
    #Cette fonction prend le graphe marvel et renvoie un dictionnaire 
    #Les cles de ce dictionnaire sont les nodes du graphe qui sont des personnages.
    #Les valeurs correspondantes sont la liste des comics à distance 1.

    dico_nodes = {}
    picon = g.getStringProperty("viewIcon")
    for n in g.getNodes():
        if(picon[n]=="md-human"):
            dico_nodes[n] = []
            neigh = g.getInOutNodes(n)
            for v in neigh : 
                dico_nodes[n].append(v)
    return(dico_nodes)


def creation_nodes(plabel,dico_nodes,color):
    #Cette fonction prend dico_nodes en argument. 
    #On veut ici créer la liste de dictionnaire que l'on renverra au html
    #Il faut donc donner les proprietes nécessaires a nos nodes
    #On a besoin de plabel pour avoir le nom des personnages.

    nodes = [] #Liste de dictionnaire. On en a besoin pour tracer le graphe avec D3
    nodes_id = {} #nodes_id est un dictionnaire. Les cles sont les nodes. Les valeurs sont l'id de ces nodes. On cree nos propres id 
    # nodes etant une liste, il est plus facile d'acceder a l'id des nodes stockees avec dictionnaire.
    id = 0
    for n in dico_nodes.keys():
        nodes_id[n] = id
        nodes.append( { "id" : id , "name" : plabel[n], "size" : 5,"color" : list(color[n]) } )
        id = id + 1
    
    return(nodes,nodes_id)



def liens(dico_nodes,nodes_id):
    # Cette fonction prend en parametre dico_nodes (le dictonnaire dont les cles sont les nodes et les valeurs les heros voisins de ces nodes)
    # Ainsi que nodes_id qui est un dictionnaire regroupant les identifiants de toutes les nodes
    # Cette fonction cree links qui est une liste de dictionnaire. C'est le format attendu pour faire le graphe en D3 
    # Chaque dictionnaire a une source et une cible, les valeurs de ces cles sont les id des nodes qui composent l'arête. 
    
    links = []
    aretes = {} #dictionnaire dont la clé est une node la valeur est la liste des aretes pour lequelles cette node est source 
    for source in dico_nodes.keys() : #on fait un parcours sur les clés du dictionnaire dico_nodes
        id_source = nodes_id[source]
        aretes[source] = []
        for target in dico_nodes[source] :
            
            id_target = nodes_id[target]
            #on veut vérifier qu'il n'existe pas d'arête de target vers source avant d'en creer une de source vers target. 

            if(target in aretes.keys()):
                # On verifie que target est bien dans les cles du dictionnaire
                # Si c'est bien le cas, on s'assure qu'il n'existe pas d'arete de target vers source
                if( source not in aretes[target]):  
                    links.append( { "source" : id_source , "target" : id_target } ) # On ajoute l'arete allant de source vers target a notre liste
                    aretes[source].append(target) # On ajoute target à la liste des aretes pour lesquelles source est l'arete source. 
            else: 
                # Target n'est pas dans les cles du dictionnaire, donc il ne peut pas exister d'arete de target vers source
                # On peut ainsi creer une arete de source vers target

                links.append( { "source" : id_source , "target" : id_target } ) # On ajoute l'arete allant de source vers target a notre liste
                aretes[source].append(target) # On ajoute target à la liste des aretes pour lesquelles source est l'arete source. 

    return(links)


### Inutile
def liens2(dico_nodes,nodes_id,nodes):
    # Cette fonction prend en parametre dico_nodes (le dictonnaire dont les cles sont les nodes et les valeurs les heros voisins de ces nodes)
    # Ainsi que nodes_id qui est un dictionnaire regroupant les identifiants de toutes les nodes
    # Cette fonction cree links qui est une liste de dictionnaire. C'est le format attendu pour faire le graphe en D3 
    # Chaque dictionnaire a une source et une cible, les valeurs de ces cles sont les id des nodes qui composent l'arête. 
    
    links = []
    for el in dico_nodes.keys() : #on fait un parcours sur les clés du dictionnaire dico_nodes
        id_source = nodes_id[el]
        for neigh in dico_nodes[el] :
            id_target = nodes_id[neigh]
            links.append( { "source" : id_source , "target" : id_target } )
        nodes[id_source]["size"] = len(dico_nodes[el])
    return(links)


def suppression_node(dico_nodes,nodes_id,links, node_personnage):
    # Cette fonction prend en paramètres dico_nodes et links
    # Le but de cette fonction est de renvoyer une copie de dico_nodes et de links
    # Sans plus que node_personnage ne soit present, ni dans l'un ni dans l'autre
    # On a besoin de cette fonction losque l'on supprime un personnage du graphe
    # Il faut alors enlever toute occurence de ce personnage de notre grahe

    id_personnage = nodes_id[node_personnage] # On récupère l'id du personnage, on en aura besoin pour supprimer dans links
    del dico_nodes[node_personnage]

    links_sans_pers = []
    for el in links: #links est une liste, on ne peut pas faire comme pour dico_nodes
        # el est un dictionnaire possedant les cles source et target
        if((el["source"] != id_personnage) and (el["target"] != id_personnage) ):
            links_sans_pers.append(el)
    return(dico_nodes,links_sans_pers)

def set_size(nodes,nodes_id,dico_nodes):
    for el in dico_nodes.keys() : #on fait un parcours sur les clés du dictionnaire dico_nodes
        id_source = nodes_id[el]
        nodes[id_source]["size"] = len(dico_nodes[el])
    return(nodes)

def graphe_marvel_tulip():
    g = tlp.loadGraph('marvel.tlpb')
    picon = g.getStringProperty("viewIcon")
    plabel = g.getStringProperty("viewLabel")

    g['viewSelection'].setAllNodeValue(False)
    heroes_dict ={} #Dictionnaire que l'on va utiliser pour augmenter le poids sur les arêtes 
    for n in g.getNodes():
        if picon[n]=='md-book-open':
            voisins = list(tlp.Graph.getInOutNodes(g,n))
            counter = 1
            for x in voisins:
                for y in voisins[counter:]: # On commence a counter pour ne pas repasser sur des nodes que l'on a deja vu
                    edge_x_y = tlp.Graph.existEdge(g,x, y, directed=True) 
                    edge_y_x = tlp.Graph.existEdge(g,y, x, directed=True)
                    if(tlp.edge.isValid(edge_x_y) or tlp.edge.isValid(edge_y_x)): # On regarde si une des 2 edge existe 
                        if(tlp.edge.isValid(edge_x_y)): #Cas 1 l'arête de x vers y existe
                            heroes_dict =tlp.Graph.getEdgePropertiesValues(g,edge_x_y)
                            heroes_dict['poids']+=1 # On augmente le poids de l'arête de 1 
                            tlp.Graph.setEdgePropertiesValues(g,edge_x_y,heroes_dict)
                        if(tlp.edge.isValid(edge_y_x)): #Cas 2 l'arête de y vers x existe 
                            heroes_dict =tlp.Graph.getEdgePropertiesValues(g,edge_y_x)
                            heroes_dict['poids']+=1 # On augmente le poids de l'arête de 1 
                            tlp.Graph.setEdgePropertiesValues(g,edge_y_x,heroes_dict)
                    else: 
                        tlp.Graph.addEdge(g,x, y,{"poids" : 1}) # On crée l'arête et on initialise son poids à 1
                counter+=1
            tlp.Graph.delNode(g,n)
    tlp.saveGraph(g,"heroes.tlpb")



def get_graph_from_char(g,personnage):
    #Le but de cette fonction est de renvoyer << l' univers >>, le graphe à distance 2, de la node passée en argument. 

    viewSelection = g.getBooleanProperty("viewSelection")
    viewSelection.setAllNodeValue(False)
    name = g.getStringProperty("viewLabel")
    # On doit récupérer la node du personnage que l'on veut 
    
    picon = g.getStringProperty("viewIcon")
    for n in picon.getNodesEqualTo("md-human"):
        if(name[n] == personnage):
            viewSelection[n] = True
            node_personnage = n

    params = tlp.getDefaultPluginParameters('Reachable SubGraph', g)
    params['edge direction'] = "all edges"
    params['distance'] = 2


    g.applyBooleanAlgorithm('Reachable SubGraph', params)
    g.addSubGraph(viewSelection, name="subGPers")
    subG = g.getSubGraph("subGPers")

    return(subG,node_personnage)

def get_node_from_char(g,personnage):
    # prend le graphe marvel en entier
    # renvoie la node du personnage et nodes_id

    picon = g.getStringProperty("viewIcon")
    plabel = g.getStringProperty("viewLabel")
    
    # On cree le dictionnaire des nodes
    # Il faut faire un id pour ces nodes
    nodes_id = {} # dictionnaire, la node est la clé et la valeur est l'id de cette node
    
    # Il faut donner un id a toutes nos nodes avant de creer les liens
    id = 0
    for n in picon.getNodesEqualTo("md-human"):
        nodes_id[n] = id
        id = id + 1
        if(plabel[n] == personnage): #On récupère la node qui correspond au nom
            node_personnage = n
    return(nodes_id,node_personnage)


def nettoyage(g,nombre):
    metricprop = g.getDoubleProperty("viewMetric")
    g.applyDoubleAlgorithm('Degree')
    for n in g.getNodes():
        if(metricprop[n]<nombre ):
            g.delNode(n)
    return(g)

def echelle_couleur():
    # On crée la liste des couleurs optimales 
    # On se base sur le site suivant 
    # https://colorbrewer2.org/#type=qualitative&scheme=Paired&n=12
    colors = []
    colors.append(tlp.Color(166,206,227))
    colors.append(tlp.Color(251,154,153))
    colors.append(tlp.Color(177,89,40))
    colors.append(tlp.Color(51,160,44))
    colors.append(tlp.Color(202,178,214))
    colors.append(tlp.Color(253,191,111))
    colors.append(tlp.Color(31,120,180))
    colors.append(tlp.Color(255,255,153))
    colors.append(tlp.Color(227,26,28))
    colors.append(tlp.Color(178,223,138))
    colors.append(tlp.Color(255,127,0))
    colors.append(tlp.Color(106,61,154))
    return (tlp.ColorScale(colors))

def tlp_color_to_hex(color):
    if(color == list(tlp.Color(166,206,227))):
        return("#a6cee3")
    if(color == list(tlp.Color(251,154,153))):
        return("#fb9a99")
    if(color == list(tlp.Color(177,89,40))):
        return("#b15928")
    if(color == list(tlp.Color(51,160,44))):
        return("#33a02c")
    if(color == list(tlp.Color(202,178,214))):
        return("#cab2d6")
    if(color == list(tlp.Color(253,191,111))):
        return("#fdbf6f")
    if(color == list(tlp.Color(31,120,180))):
        return("#1f78b4")
    if(color == list(tlp.Color(255,127,0))):
        return("#ff7f00")
    if(color == list(tlp.Color(255,255,153))):
        return("#ffff99")
    if(color == list(tlp.Color(227,26,28))):
        return("#e31a1c")
    if(color == list(tlp.Color(178,223,138))):
        return("#b2df8a")
    if(color == list(tlp.Color(106,61,154))):
        return("#6a3d9a")
    return
    
def coloration(Nodes):
    for n in Nodes :
        community = n["communauté"]
        # On attribue une couleur en fonction de la valeur de la communauté
        if(community == 0):
            n["color"]="#a6cee3"               
        if(community == 1):
            n["color"]="#1f78b4"
        if(community == 2):
            n["color"]="#b2df8a"
        if(community == 3):
            n["color"]="#33a02c"
        if(community == 4):
            n["color"]="#fdbf6f"
        if(community == 5):
            n["color"]="#e31a1c"
        if(community == 6):
            n["color"]="#fb9a99"
        if(community == 7):
            n["color"]="#ff7f00"
        if(community == 8):
            n["color"]="#cab2d6"
        if(community == 9):
            n["color"]="#b15928"
        if(community == 10):
            n["color"]="#ffff99"
        if(community == 11):
            n["color"]="#6a3d9a"  
    return(Nodes)
    
            
            
            

############## ROUTES ##############
    
@app.route("/")
def home():
    g = tlp.loadGraph('marvel.tlpb')
    global dico_nodes 
    dico_nodes = graphe_marvel_sans_comics(g) 
    plabel = g.getStringProperty("viewLabel")
    color =  g.getColorProperty("viewColor")
    global nodes
    global nodes_id
    global links
    (nodes,nodes_id) = creation_nodes(plabel,dico_nodes,color) 
    links = liens(dico_nodes,nodes_id)

    # A modifier, ici on veut load le graphe une seule fois,
    # Faire en sorte que les fonctions se basent sur le graphe
    # g = tlp.loadGraph('heroes.tlpb')

    return render_template("home.html", title="Home")


@app.route("/getCloud")
def getCloud():

    # load graph data
    g = tlp.loadGraph('spiderman.tlpb')
    
    #compute node degree
    metricprop = g.getDoubleProperty("viewMetric")
    g.applyDoubleAlgorithm("Degree", metricprop)
    #g.applyDoubleAlgorithm("Betweenness Centrality", metricprop)
    
    #get 15 characters with the highest Degree (most published)
    picon = g.getStringProperty("viewIcon")
    plabel = g.getStringProperty("viewLabel")
    val={}
    for n in picon.getNodesEqualTo("md-human"):
        val[plabel[n]]=int(metricprop[n])
    best = OrderedDict(sorted(val.items(), key=lambda t: t[1], reverse=True)) 
    best15 = list(islice(best.items(),50))

    #produce a csv  return it
    csvdata = io.StringIO()
    writer = csv.writer(csvdata,delimiter=",")
    
    writer.writerow(("name", "val"))
    for n in best15:
        writer.writerow(n)
    
    output = make_response(csvdata.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=data_wc_marvel.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route("/cloud")
def cloud():
    return render_template("word_cloud.html",title="Nuage de mots des meilleurs amis de Spider-man")




@app.route("/getForce")
def getForce():
    g = tlp.loadGraph('marvel.tlpb') #Fonctionne 


    #### Temporaire #### 
    personnage = "Spider-Man"
    (subG,node_p) = get_graph_from_char(g,personnage)
    ####################

    #Ce bloc est a remplacer une fois que l'utilisateur peut lui meme choisir le personnage qu'il veut 

    plabel = g.getStringProperty("viewLabel")
    #dico_nodes = graphe_marvel_sans_comics(g) #Fonctionne 
    dico_nodes = graphe_marvel_sans_comics(subG) # Fonctionne


    color =  g.getColorProperty("viewColor")
    (nodes,nodes_id) = creation_nodes(plabel,dico_nodes,color) #Fonctionne 
    links = liens(dico_nodes,nodes_id)
    
    # Je suis pas certain qu'on veuille mapper la taille ici
    #nodes = set_size(nodes,nodes_id,dico_nodes)


    ##### Temporaire ##### 
    # on montre les 50 personnages du graphe d'amis de Spiderman
    # On recup les X nodes de plus haut degre
    nodes = sorted(nodes, key=lambda t: t['size'], reverse=True)
    nodes_sliced = list(islice(nodes,50))
    nodes_sliced = list(islice(nodes,150))
    nodes_sliced = sorted(nodes_sliced, key=lambda t: t['size'], reverse=False)
    nodes_sliced = list(islice(nodes_sliced,60))


    # On recupere juste les heros qui nous intéressent
    id_sliced_nodes = []
    for el in nodes_sliced : 
        id_sliced_nodes.append(el["id"])
    links_sliced = []
    for el in links : # el est un dictionnaire 
        if( (el["source"] in id_sliced_nodes) and (el["target"] in id_sliced_nodes) ):
            links_sliced.append(el)

    ##### Temporaire #####

    dico = {}
    dico["nodes"] = nodes_sliced
    dico["links"] = links_sliced

    resp = json.dumps(dico) # resp = json.dumps(nodes) + json.dumps(links)

    output = make_response(resp)
    output.headers["Content-Disposition"] = "attachment; filename=force_directed_graph.json"
    output.headers["Content-type"] = "json"
    return output

@app.route("/force")
def force():
    return render_template("force_directed_graph.html",title="Force-Directed Graph")


@app.route("/globale1")
def globale1():
    return render_template("globale1.html",title="Etude Globale")

@app.route("/getGlobale1")
def getGlobale1():
    # load graph data
    #g = tlp.loadGraph('marvel.tlpb')
    #plabel = g.getStringProperty("viewLabel")
    
    global dico_nodes
    global nodes 
    global links
    global nodes_id

    nodes = set_size(nodes,nodes_id,dico_nodes)

    
    ## Enlever les nodes sans voisins. 
    dico = {}
    dico["nodes"] = nodes
    dico["links"] = links   
    resp = json.dumps(dico) # resp = json.dumps(nodes) + json.dumps(links)
    output = make_response(resp)
    output.headers["Content-Disposition"] = "attachment; filename=globale1.json"
    output.headers["Content-type"] = "json"    
    return output

   

@app.route("/louvain")
def louvain():
    return render_template("louvain.html",title="Communautés")

@app.route("/getLouvain")
def getLouvain():
    # On charge les données du graphe
    g = tlp.loadGraph('heroes.tlpb')
    plabel = g.getStringProperty("viewLabel")
    metricprop = g.getDoubleProperty("viewMetric")
    layout = g.getLayoutProperty("viewLayout")
    # On réalise le nettoyage des données
    # On ne conserve que les nodes ayant un degre suffisant
    # Les nodes qui ont un degre trop petit ne font pas assez partie du reseau social
    
    g = nettoyage(g,300)
    
    # Ce filtrage est un peu artificiel, il nous permet de passer de 38 communautés sans filtrage 
    # A 8 communautés après. Il est impossible de representer clairement 38 communautés avec des couleurs 

    
    #On veut faire en sorte que notre algo prenne en compte le poids des arêtes pour créer les commus
    params = tlp.getDefaultPluginParameters('Louvain', g)
    poids = g.getIntegerProperty("poids")
    params['metric'] = poids

    g.applyDoubleAlgorithm('Louvain',params)
    
    
    # On a appliqué l'algo de Louvain a notre graphe. Dans view Metric se trouve le numero de la commu
    # Attention, le nombre de commus ne doit pas etre plus grand que 12  
    color_scale = echelle_couleur()    


    params2 = tlp.getDefaultPluginParameters('Color Mapping', g)
    params2["color scale"] = color_scale
    color =  g.getColorProperty("viewColor")
    
    g.applyColorAlgorithm('Color Mapping',params2)
    #Maintenant, on a une couleur différente pour chaque communauté 
    
    #On applique l'algo FM^3 (OGDF) pour dessiner le graphe en regroupant les communautés
    g.applyLayoutAlgorithm('FM^3 (OGDF)')
    
    #On recupère les dictionnaires des nodes et des arêtes et on trace le graphe
    dico_Nodes = graphe_heros_sans_comics(g)
    

    Nodes = [] #Liste de dictionnaire. On en a besoin pour tracer le graphe avec D3
    Nodes_id = {} #nodes_id est un dictionnaire. Les cles sont les nodes. Les valeurs sont l'id de ces nodes. On cree nos propres id 
    # nodes etant une liste, il est plus facile d'acceder a l'id des nodes stockees avec dictionnaire.
    id = 0
    for n in dico_Nodes.keys():
        Nodes_id[n] = id
        Nodes.append( { "id" : id , "name" : plabel[n], "size" : 5,"color" : list(color[n]),"communauté" : metricprop[n],"x" : layout[n][0],"y" :layout[n][1]  } )
        id = id + 1
    
    Nodes = coloration(Nodes)
    
    for n in Nodes:
        n["size"] = 50

    
    Links = liens(dico_Nodes,Nodes_id)

    print("le nombre de communautés est : ",params["#communities"])
    print("la maudularité vaut : ",params["modularity"])
    
    
    # on renvoie le json 
    dico = {}
    dico["nodes"] = Nodes
    dico["links"] = Links   
    resp = json.dumps(dico) # resp = json.dumps(nodes) + json.dumps(links)
    output = make_response(resp)
    output.headers["Content-Disposition"] = "attachment; filename=louvain.json"
    output.headers["Content-type"] = "json"    
    return output











## Route de Test ## 



@app.route("/test")
def test():
    return render_template("etude_de_cas.html") 

@app.route("/getTest")
def getTest(): 
    # # route pour tester si les choses fonctionnent bien comme on le veut 

    # # test pour savoir si graphe_marvel_avec_comics fonctionne normalement

    # g = tlp.loadGraph('marvel.tlpb')
    # plabel = g.getStringProperty("viewLabel")
    
    # dico_nodes = graphe_marvel_avec_comics(g) 
    # print(len(dico_nodes))
    
    
    # s = 0
    # for n in dico_nodes.keys(): #Les clés de dico_nodes sont les heros
    #     print(len(dico_nodes[n]))
    #     s += 1 
    # print("comparons mnt s et dico_nodes")
    # print(s)
    # print(len(dico_nodes)) 
    # #dico_nodes est donc non vide, fonctionne 

    # # Test pour voir suppression_node fonctionne 
    # # On va supprimer spiderman de son univers

    
    # personnage = "Spider-Man"
    # (subG,node_p) = get_graph_from_char(g,personnage)
    # plabel = g.getStringProperty("viewLabel")
    # dico_nodes = graphe_marvel_sans_comics(subG) # Fonctionne
    # color =  g.getColorProperty("viewColor")
    # (nodes,nodes_id) = creation_nodes(plabel,dico_nodes,color) #Fonctionne 
    # links = liens(dico_nodes,nodes_id)

    # (dico_nodes_apres_suppression, links_apres_suppression) = suppression_node(dico_nodes,nodes_id,links, node_p)

    # output = ""
    # for n in dico_nodes.keys():
    #     output = output + plabel[n] + "<br>"
    # print("Les personnages dans dico_nodes apres suppression sont au nombre de :")
    # print(len(dico_nodes))
    # #Quand on regarde les heros presents apres suppression, Spider-Man n'est pas present
    # #On a effectivement perdu 1 sur len dico_nodes
    # #Il faudrait s'assurer que c'est le cas aussi dans links


    

    graphe_marvel_tulip()
    g = tlp.loadGraph('heroes.tlpb')
    tlp.saveGraph(g,"heroes.tlpx")


    plabel = g.getStringProperty("viewLabel")

    output = ""
    compteur = 0
    for n in g.getNodes():
        output = output + plabel[n] + "<br>"
        compteur += 1
    print(compteur)
    return output

## Fin Route de Test ## 
























@app.route("/getTree")
def getTree():
    # Ici, on veut calculer le degré de chaque personnage de l'univers, ainsi que la somme de ces degrés
    # On fait ensuite un dictionnaire ordonné par la valeur du degré
    # On prend assez de personnages pour avoir 50% de la somme des degrés totaux


    # load graph data
    g = tlp.loadGraph('marvel.tlpb')
    
    #compute node degree
    metricprop = g.getDoubleProperty("viewMetric")
    g.applyDoubleAlgorithm("Degree", metricprop)
    
    #get 15 characters with the highest Degree (most published)
    picon = g.getStringProperty("viewIcon")
    plabel = g.getStringProperty("viewLabel")
    val={}
    deg_total = 0
    for n in picon.getNodesEqualTo("md-human"):
        val[plabel[n]]=int(metricprop[n])
        deg_total = deg_total + int(metricprop[n])
        
    best = OrderedDict(sorted(val.items(), key=lambda t: t[1], reverse=True)) 
   
    #half = deg_total/2
    half = deg_total/3

    sum = 0
    main_char = []
    while(sum < half):
        #on recup les personnages qui sont les plus importants
        el = best.popitem(last=False)
        # cle valeur  == nom degre 
        main_char.append([el[0],el[1]])
        sum = sum + el[1]

    # attention, en faisant comme ça, on peut depasser half et donc avoir plus de la moitié des publications
   
    #produce a csv  return it
    csvdata = io.StringIO()
    writer = csv.writer(csvdata,delimiter=",")
    
    writer.writerow(("name","parent", "value"))
    writer.writerow(("Marvel","",""))
    for h in main_char:
        nom = str(h[0])
        score = str(h[1])
        #writer.writerow((nom,"personnages principaux",score))
        writer.writerow((nom,"Marvel",score))


    
    output = make_response(csvdata.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=data_wc_marvel.csv"
    output.headers["Content-type"] = "text/csv"
    return output
    

@app.route("/tree")
def tree():
    return render_template("treemap.html",title="Treemap")



@app.route("/getRatioData")
def getRatio():
    #load graph data
    graph = tlp.loadGraph('marvel.tlpb')
    dico_nodes = {}
    dico_nodes_0_doublon = {}
    # dictionnaire dans lequel la clé est une node 
    # et la valeur est la liste d'adjacence de distance 2 de cette node. 
    picon = graph.getStringProperty("viewIcon")
    # On ne s'intéresse qu'aux heros 
    for n in picon.getNodesEqualTo("md-human") : 
        dico_nodes[n] = []
        dico_nodes_0_doublon[n] = [] 
        neigh = graph.getInOutNodes(n) 
        # On récupère tous les comics dans lequel le hero apparaît
        for v in neigh : 
            #on récupère tous les heros de ce comic, sauf n 
            #on les met dans la liste d'adj si ils n'y sont pas deja
            v_neigh = graph.getInOutNodes(v)
            for u in v_neigh : 
                # Changer pour mettre un poids à la place
                if(u != n):
                    dico_nodes[n].append(u)
                    if(u not in dico_nodes_0_doublon[n]):
                        dico_nodes_0_doublon[n].append(u)

    ratio = []
    for n in dico_nodes:
        if( len(dico_nodes[n])!=0):
            ratio.append(len(dico_nodes_0_doublon[n])/len(dico_nodes[n]))
        else:
            ratio.append(0)

    ratio_dispersion = [0,0,0,0,0,0,0,0,0,0,0]
    
    for i in ratio :
        i=i*10 
        i= int(i)
        ratio_dispersion[i] = ratio_dispersion[i] + 1

    #produce a csv  return it
    csvdata = io.StringIO()
    writer = csv.writer(csvdata,delimiter=",")
    writer.writerow(["ratio", "quantite"])
    for n in range(len(ratio_dispersion)-1):
        writer.writerow(([n/10, n/10 + 0.1], ratio_dispersion[n]))

    output = make_response(csvdata.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=data_histo_marvel.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route("/barchart")
def barchart():
    return render_template("barchart.html", title="Quantité de personnages en fonction du ratio nombre d'amis sur nombre de relations")





@app.route("/getHistoData")
def getData():
	#load graph data
	graph = tlp.loadGraph('marvel.tlpb')
	dico_nodes = {}
	dico_nodes_0_doublon = {}
	# dictionnaire dans lequel la clé est une node 
	# et la valeur est la liste d'adjacence de distance 2 de cette node. 
	picon = graph.getStringProperty("viewIcon")
	# On ne s'intéresse qu'aux heros 
	for n in picon.getNodesEqualTo("md-human") : 
		dico_nodes[n] = []
		dico_nodes_0_doublon[n] = [] 
		neigh = graph.getInOutNodes(n) 
		# On récupère tous les comics dans lequel le hero apparaît
		for v in neigh : 
			#on récupère tous les heros de ce comic, sauf n 
			#on les met dans la liste d'adj si ils n'y sont pas deja
			v_neigh = graph.getInOutNodes(v)
			for u in v_neigh : 
				# Changer pour mettre un poids à la place
				if(u != n):
					dico_nodes[n].append(u)
					if(u not in dico_nodes_0_doublon[n]):
						dico_nodes_0_doublon[n].append(u)    
	#return([dico_nodes,dico_nodes_0_doublon])
	
	# On veut les noms des personnages plutot que les nodes
	#plabel = g.getStringProperty("viewLabel") 

	#produce a csv  return it
	csvdata = io.StringIO()
	writer = csv.writer(csvdata,delimiter=",")
	writer.writerow( ["character", "nb_relat", "nb_amis"])
	for n in dico_nodes:
		writer.writerow( [n, len(dico_nodes[n]), len(dico_nodes_0_doublon[n]) ] )
	
	output = make_response(csvdata.getvalue())
	output.headers["Content-Disposition"] = "attachment; filename=data_histo_marvel.csv"
	output.headers["Content-type"] = "text/csv"
	return output
	
	

@app.route("/scatter")
def scatter():
	return render_template("scatter.html", title="Nombre de relations et nombre d'amis")





#NE SURTOUT PAS MODIFIER OU DEPLACER, TOUT AJOUT DE CODE DOIT ETRE EFFECTUE AU DESSUS DE CES LIGNES
if __name__ == "__main__":
   #app.run(debug=True, host='0.0.0.0', port=5000)
     app.run(debug=True)
