"""
Fonctions d'extraction d'informations depuis les factures PDF.
Ce fichier contient toutes les fonctions spécifiques aux fournisseurs.
"""

import fitz

# =============================================================================
# RELAIS VERT => avoir ok
# =============================================================================
def fonction_relais_vert(doc) :
    # On sélectionne la dernière page du document
    derniere_page = doc[-1]
    
    # Récupération des blocs de texte de la dernière page
    blocs_text = derniere_page.get_text("blocks")
    
    # On cherche le bloc qui nous intéresse avec une liste de mots clés (il n'apparait pas en dernier dans la liste des blocks)
    mots_cles_1 = ['Client', 'Facture', 'Date', 'Montant']
    mots_cles_2 = ['Client', 'Avoir', 'Date', 'Montant']
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        # Vérifier si tous les mots-clés sont présents dans ce bloc
        if all(mot in texte_bloc for mot in mots_cles_1):
            infos = texte_bloc
            break # on sort de la boucle for dès qu'on a trouvé
        if all(mot in texte_bloc for mot in mots_cles_2): #Si on a pas trouvé on cherche avec les mots clés 2
            infos = texte_bloc
            break # on sort de la boucle for dès qu'on a trouvé
    # On met les infos dans un dataframe
        # On fait un premier split avec le tiret
    infos_split = infos.split(' - ')
        # On supprime les espaces avant et après, et le symbole €
    infos_split = [mot.replace('€','').replace('\n"','').strip() for mot in infos_split]
        # On split chaque élément de la liste info_split par espace et on garde le dernier mot à chaque fois
    infos_def = [a.split(' ')[-1] for a in infos_split]
        # on renvoie les infos qui nous intéressent pour alimenter le df, qui est une liste ['numéro Facture', 'Date', 'Montant']
    return infos_def[1:]

# =============================================================================
# RELAIS LOCAL => avoir ok
# =============================================================================
def fonction_relais_local(doc) :
    # On ouvre la première page
    premiere_page = doc[0]
    # Récupération des blocs de texte de première page
    blocs_text = premiere_page.get_text("blocks")
    
    # Récupération du numéro de facture
    mot_cle_1 = 'Facture N°'
    mot_cle_2 = 'Avoir N°'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) or (mot_cle_2 in texte_bloc) :
            infos = texte_bloc
            break
    # On isole le numéro et on le met dans une variable
    num_fact = infos.split(' ')[-1]
    
    # Recherche de la date
        # Utilisation des coordonnées trouvées avec les lignes en commentaire ci-dessous
    bbox_date = (348.75, 48.44, 465, 88.15) # coordonnées x0, y0, x1, y1 du bloc qui contient la date
    zone_date = fitz.Rect(bbox_date)
        # Récupérer le texte dans cette zone
    texte_date = premiere_page.get_text("text", clip=zone_date)
    texte_date_split = texte_date.split('\n')
    date = [mot for mot in texte_date_split if "/" in mot][0]
    
    # Recherche du montant
        # On va à la dernière page
    derniere_page = doc[-1]  
        # Utilisation des coordonnées trouvées ci-dessus et recherche de texte dans la zone
    bbox_montant = (369.7, 751.9, 544.5, 761.5) # coordonnées x0, y0, x1, y1 du bloc qui contient le montant
    zone_montant = fitz.Rect(bbox_montant)
        # Récupérer le texte dans cette zone
    texte_montant = derniere_page.get_text("text", clip=zone_montant)
        # On identifie si c'est une facture débit ou crédit
    if "NET A PAYER" in texte_montant : 
        signe = 1
    elif "NET A DEDUIRE" in texte_montant :
        signe = -1
    else : 
        raise ValueError(f"Signe (débit ou crédit) non identifié dans la facture relais local")
    texte_montant_split = texte_montant.split('\n')
    montant = [mot for mot in texte_montant_split if "," in mot][0]
    if signe == -1 :
        montant = '-' + montant

    return [num_fact, date, montant]

# =============================================================================
# LA BASSE COUR => pas d'exemple avec avoir
# =============================================================================
def fonction_basse_cour(doc) :
    # On ouvre la première page
    premiere_page = doc[0]
    
    # Récupération des blocs de texte de première page
    blocs_text = premiere_page.get_text("blocks")
    
        # Récupération de la date et du numéro de facture
    mot_cle = 'DEMAIN SUPERMARCHE - '
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if mot_cle in texte_bloc :
            infos = texte_bloc
            break
        # On split pour récupérer nos infos
    date = infos.split(' - ')[1]
    num_fact = infos.split(' - ')[-1].split('_')[-1]
        
    # Récupération du montant
        # On ouvre la dernière page
    derniere_page = doc[-1]
        # Récupération des blocs de texte de dernière page
    blocs_text = derniere_page.get_text("blocks")
    mot_cle = 'Total TTC'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if mot_cle in texte_bloc :
            infos = texte_bloc
            break
        # On split pour récupérer le montant, et on remplace le . par , pour être cohérent avec les autres fichiers
    montant = infos.split('\n')[-1].replace('.',',').replace('€','').strip()
    return [num_fact, date, montant]

# =============================================================================
# ANDRIC => si c'est scanné on ne traite pas pour le moment => pas d'exemple avec avoir
# =============================================================================
def fonction_andric(doc) :
    premiere_page = doc[0]
    
    # Récupération de la date et numéro de commande
    bbox = (118.2, 295.99, 230, 306.98)
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = premiere_page.get_text("text", clip=zone)
        # on split
    date = infos.split('\n')[0]
    num_fact = infos.split('\n')[1]
    
        
    # Récupération du montant => ce n'est pas forcément la dernière page car on a un exemple avec une dernière page qui contient des infos lambdas, et ça ne sera peut être pas toujours la première page
        # => on boucle sur toutes les pages pour être sûr de trouver
    trouve = 0
    for num_page in range(len(doc)) :
        if trouve == 1 :
            break
        # Initialisation de la page
        page = doc[num_page]
        # Récupération des blocs de texte de la page
        bbox = (364.82, 763.32, 528.26, 777.04)
        zone = fitz.Rect(bbox)
            # Récupérer le texte dans cette zone
        infos = page.get_text("text", clip=zone)
            # On vérifie qu'on a bien trouvé le montant sinon on passe à la page suivante
        if "TOTAL TTC" in infos and "€" in infos : 
            trouve = 1
            montant = infos.split('\n')[1].replace('€','').strip()
          
    return [num_fact, date, montant]

# =============================================================================
# SALAISONS DE CHARTREUSE => pas d'exemple avec avoir
# =============================================================================
def fonction_salaisons_de_chartreuse(doc) :
    # On ouvre la première page
    premiere_page = doc[0]

    # Récupération de la date et numéro de commande
    bbox = (400.81, 69.23, 466.512, 97.89)
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = premiere_page.get_text("text", clip=zone)
    num_fact = infos.split('\n')[0]
    date = infos.split('\n')[1]
        
    # Récupération du montant
        # On ouvre la dernière page
    derniere_page = doc[-1]
        # Récupération des blocs de texte de dernière page
    blocs_text = derniere_page.get_text("blocks")
    mot_cle = 'Montant total TTC'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if mot_cle in texte_bloc :
            infos = texte_bloc
            break
        # On split pour récupérer le montant, et on remplace le . par , pour être cohérent avec les autres fichiers
    montant = infos.split('\n')[-1].replace('€','').strip()
    return [num_fact, date, montant]

# =============================================================================
# EKIBIO => avoir ok
# =============================================================================
def fonction_ekibio(doc) :
   # Recherche de la date et du numéro de facture
    premiere_page = doc[0]
    blocs_text = premiere_page.get_text("blocks")
    mot_cle_1 = 'FACTURE No'
    mot_cle_2 = 'AVOIR No'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) or (mot_cle_2 in texte_bloc) :
            infos = texte_bloc
            break
        # On fait un 1er split par saut de ligne = la date est dans le 2e élément, le numéro dans le 3e
    infos = infos.split('\n')
    num_fact = infos[2].strip()
    date = infos[1].strip().split(' ')[1].strip()
        # L'année de la date est au format AA => on remet 20 devant => il faudra changer en 2030 si on utilise encore ce script d'ici là !
    date = date[:-2] + '20' + date[-2:]
        
    # Récupération du montant => c'est plus compliqué ici car le mot clé ne donne pas le montant, et que la position est différente sur chaque facture
        # On a un exemple (996060) avec une page vide à la fin, donc on va faire aussi sur l'avant dernière
    trouve = 0
    for n in [-1,-2] : 
        derniere_page = doc[n]
            # Récupération des blocs de texte de dernière page
        blocs_text = derniere_page.get_text("blocks")
            # On définit le delta de coordonnées qu'on a calculé avec un exemple
        delta = [5.70001220703125, 13.8699951171875, 0.0076904296875, 13.8699951171875]
            # On cherche d'abord la position du mot clé "Total TTC" pour obtenir celle du montant
        mot_cle = 'Total TTC'
        for bloc in blocs_text:
            texte_bloc = bloc[4].strip()
            if mot_cle in texte_bloc :
                trouve = 1
                bbox_0 = bloc[0:4] # On récupère les coordonnées de l'emplacement "Total TTC"
                bbox = [sum(x) for x in zip(bbox_0, delta)] # On définit la position avec celle du texte "Total TTC" + le delta
                break
        if trouve == 1 :
            break
        # On cherche le montant à partir de la position trouvée
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = derniere_page.get_text("text", clip=zone)
    montant = infos.strip()
    
    return [num_fact, date, montant]

# =============================================================================
# EPICE => avoir ok
# =============================================================================
def fonction_epice(doc) :
    premiere_page = doc[0]
 
    # Récupération de la date et du numéro de facture
    bbox = (37.80015563964844, 181.5373992919922, 394.8822326660156, 192.17526245117188)
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = premiere_page.get_text("text", clip=zone)
    infos_split = infos.split('\n')
    num_fact = infos_split[1]
    date = infos_split[2]
    date = date[:-2] + '20' + date[-2:]

          
    # Récupération du montant
        # On ouvre la dernière page
    derniere_page = doc[-1]
        # Récupération des blocs de texte de dernière page
    blocs_text = derniere_page.get_text("blocks")
    mot_cle_1 = 'NET A PAYER'
    mot_cle_2 = 'Montant à déduit de votre prochaine facture'
    trouve = 0
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if mot_cle_1 in texte_bloc :
            infos = texte_bloc
            if "," in infos : # Il y a deux fois le mot clé dans la facture, mais un seul bloc contient le montant : on sélectionne celui qui contient aussi le montant grace à la virgule
                trouve = 1
                break
        if mot_cle_2 in texte_bloc :
            infos = texte_bloc
            trouve = -1
            break
        # Récupération du montant
    if trouve == 1 : 
        montant = infos.split('\n')[-1]
    elif trouve == -1 : 
        montant = '-' + infos.split('\n')[0]
    return [num_fact, date, montant]

# =============================================================================
# COOP LAITIERE DE YENNE => avoir ok
# =============================================================================
def fonction_coop_yenne(doc) :
    # On ouvre la première page
    premiere_page = doc[0]
    blocs_text = premiere_page.get_text("blocks")

    # Récupération de la date et du numéro de facture
    mot_cle_1 = 'Facture n°'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break
    infos = infos.split('\n')
    date = infos[1]
    num_fact = infos[-1]
        
    # Récupération du montant
        # On ouvre la dernière page
    derniere_page = doc[-1]
    bbox = (504.4800109863281, 727.0875244140625, 541.384521484375, 739.0863037109375)
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = derniere_page.get_text("text", clip=zone)
    montant = infos.strip()
    return [num_fact, date, montant]

# =============================================================================
# AGIDRA  => pas d'exemple avec avoir
# =============================================================================
def fonction_agidra(doc) :
    premiere_page = doc[0]

    # Récupération du numéro de facture
    bbox = (126.19999694824219, 100.09099578857422, 193.38148498535156, 108.80359649658203)
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = premiere_page.get_text("text", clip=zone)
    num_fact = infos.strip().replace('/','_') # on remplace le / par _ sinon on va avoir des problèmes pour les chemins
    
    # Récupération de la date
    bbox = (127.19999694824219, 127.51949310302734, 409.3546142578125, 152.66717529296875)
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = premiere_page.get_text("text", clip=zone)
    date = infos.split('\n')[0].strip()
    
    # Récupération du montant
    derniere_page = doc[-1]
    blocs_text = derniere_page.get_text("blocks")
    mot_cle_1 = 'NET À PAYER'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break
    infos = infos.split('\n')
    montant = infos[1].strip()
    
    return [num_fact, date, montant]

# =============================================================================
# DDS  => avoir ok
# =============================================================================
def fonction_dds(doc) :
    # On ouvre la première page
    premiere_page = doc[0]
    blocs_text = premiere_page.get_text("blocks")

    # Récupération de la date et du numéro de facture 
    mot_cle_1 = 'N°Facture'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break
    infos_split = infos.split('\n')
    date = infos_split[2]
    num_fact = infos_split[3]  
    
    # Récupération du montant
    derniere_page = doc[-1]
    bbox = (520.1199951171875, 705.8599853515625, 559.8741455078125, 743.68701171875) # coordonnées x0, y0, x1, y1 du bloc qui contient le montant
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = derniere_page.get_text("text", clip=zone)
    montant = infos.strip().replace('.',',')
            
    return [num_fact, date, montant]

# =============================================================================
# GRAP => pas d'exemple avec avoir
# =============================================================================
def fonction_grap(doc) : 
    # On ouvre la première page
    premiere_page = doc[0]
    blocs_text = premiere_page.get_text("blocks")

    # Récupération du numéro de facture 
    mot_cle_1 = 'Facture'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break
    num_fact = infos.split(' ')[-1].replace('/','_') # on remplace les / par _ sinon problème dans le chemin du fichier
    
    # Récupération de la date
    bbox = (32.167015075683594,215.63381958007812,412.79888916015625,225.87973022460938)
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = premiere_page.get_text("text", clip=zone)
    date = infos.split('\n')[0].strip()
        
    # Récupération du montant
    derniere_page = doc[-1]
    blocs_text = derniere_page.get_text("blocks")
    mot_cle_1 = 'Total'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break
    montant = infos.split('\n')[-1].replace('€','').strip()
        
    return [num_fact, date, montant]

# =============================================================================
# FULCHIRON / PATRIMONIAM => ce sont les mêmes modèles, j'ai l'impression que maintenant c'est toujours fulchiron, à confirmer avec JM => pas d'exemple avec avoir
# =============================================================================
def fonction_fulchiron(doc) : 
    # On ouvre la première page
    premiere_page = doc[0]
    blocs_text = premiere_page.get_text("blocks")

    # Récupération du numéro de facture 
    mot_cle_1 = 'FACTURE N°'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break
    num_fact = infos.split('°')[-1]
    

    # Récupération de la date
    mot_cle_1 = "Date d'Emission"
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break
    date = infos.split(' ')[-1]
    
    
    # Récupération du montant
    derniere_page = doc[-1]
    blocs_text = derniere_page.get_text("blocks")
    mot_cle_1 = 'Total TTC'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break
    montant = infos.split(' : ')[-1].replace('€','').strip()
        
    return [num_fact, date, montant]

# =============================================================================
# T'AIR DE FAMILLE => pas d'exemple avec avoir
# =============================================================================
def fonction_tair_famille(doc) :
    # On ouvre la première page
    premiere_page = doc[0]
    blocs_text = premiere_page.get_text("blocks")

    # Récupération du numéro de facture 
    bbox = (236.2899932861328,166.95729064941406,290.9638366699219,177.6246337890625)
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = premiere_page.get_text("text", clip=zone)
    num_fact = infos.strip()
    
    # Récupération de la date
    mot_cle_1 = "Date :"
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break
    date = infos.split(':')[-1].strip()
    
        # Récupération du montant
    derniere_page = doc[-1]
    bbox = (527.3400268554688,765.6544189453125,568.0888061523438,777.5460815429688)
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = derniere_page.get_text("text", clip=zone)
    montant = infos.replace('€','').strip()
        
    return [num_fact, date, montant]

# =============================================================================
# CAVE BIO => avoir ok
# =============================================================================
def fonction_cave_bio(doc) :
   # Il faut d'abords identifier si c'est un avoir ou une facture
    # On ouvre la dernière page => y'a des mots en fond sur les factures, et celui que j'utilise est présent en première page même quand c'est pas un avoir
    derniere_page = doc[-1]
    blocs_text = derniere_page.get_text("blocks")
    top_avoir = 0 
    mot_cle_1 = "A DEDUIRE"
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            top_avoir = 1
            break
       
    # On ouvre la première page
    premiere_page = doc[0]
    blocs_text = premiere_page.get_text("blocks")
    # Si c'est un avoir
    if top_avoir == 1 :
        # Récupération du numéro et de la date
        mot_cle_1 = "AVOIR n°"
        for bloc in blocs_text:
            texte_bloc = bloc[4].strip()
            if (mot_cle_1 in texte_bloc) :
                infos = texte_bloc
                break
        num_fact = infos.split(' ')[2]
        date = infos.split(' ')[4]
        
        # Récupération du montant      
        derniere_page = doc[-1]
        bbox = (509.2799987792969,665.75,545.8001098632812,679.52001953125)
        zone = fitz.Rect(bbox)
            # Récupérer le texte dans cette zone
        infos = derniere_page.get_text("text", clip=zone)
        montant = infos.replace('€','').replace(' ','').strip()       
   
   # Si c'est une facture : 
    if top_avoir == 0 :
        # Récupération de la date
        bbox = (39.599998474121094,153.38502502441406,114.62399291992188,163.4380340576172)
        zone = fitz.Rect(bbox)
            # Récupérer le texte dans cette zone
        infos = premiere_page.get_text("text", clip=zone)
        date = infos.strip()
        jour = date.split(' ')[0]
        mois = date.split(' ')[1]
        annee = date.split(' ')[2]
        dict_mois = {'janvier' : '01',
                    'février' : '02',
                    'mars' : '03',
                    'avril' : '04',
                    'mai' : '05',
                    'juin' : '06',
                    'juillet' : '07',
                    'août' : '08',
                    'septembre' : '09',
                    'octobre' : '10',
                    'novembre' : '11',
                    'décembre' : '12',
                    }
        date = f"{jour}/{dict_mois[mois]}/{annee}"
    
        # Récupération du numéro de facture
        bbox = (172.32000732421875, 153.38502502441406, 219.84898376464844, 163.4380340576172)
        zone = fitz.Rect(bbox)
            # Récupérer le texte dans cette zone
        infos = premiere_page.get_text("text", clip=zone)
        num_fact = infos.strip().replace(' ','')
        
        # Récupération du montant
        derniere_page = doc[-1]
        blocs_text = derniere_page.get_text("blocks")
        mot_cle_1 = "Total TTC"
        for bloc in blocs_text:
            texte_bloc = bloc[4].strip()
            if (mot_cle_1 in texte_bloc) :
                infos = texte_bloc
                break
        montant = infos.split('\n')[1].replace('€', '').replace(' ','').strip()
        
    return [num_fact, date, montant]

# =============================================================================
# BRASSERIE DU PILAT => pas trouvé d'exemple avec avoir
# =============================================================================
def fonction_brasserie_pilat(doc) :
    # On ouvre la première page
    premiere_page = doc[0]   
    
    # Récupération de la date et du numéro de facture 
    bbox = (7.6666998863220215,258.432373046875,432.4901123046875,268.7391052246094)
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = premiere_page.get_text("text", clip=zone)
    date = infos.split('\n')[1]
    num_fact = infos.split('\n')[2]

    # Récupération du montant
    derniere_page = doc[-1]
    blocs_text = derniere_page.get_text("blocks")
    mot_cle_1 = "***"
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break
    montant = infos.replace('*','').strip()
        
    return [num_fact, date, montant]

# =============================================================================
# ECODIS => avoir ok
# =============================================================================
def fonction_ecodis(doc) :
    # On ouvre la première page
    premiere_page = doc[0]   
    blocs_text = premiere_page.get_text('blocks')
    
    # On regarde si c'est une facture ou un avoir
    top_avoir = 0
    mot_cle_1 = 'AVOIR'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            top_avoir = 1
            break 

    # Récupération du numéro de facture
    bbox = (47.81999969482422,166.83001708984375,79.22399139404297,179.2230224609375)
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = premiere_page.get_text("text", clip=zone)
    num_fact = infos.strip()
    
    # Récupération de la date
    bbox = (140.94000244140625,166.78501892089844,274.1039733886719,179.15101623535156)
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = premiere_page.get_text("text", clip=zone)
    date = infos.split('\n')[1].strip()

    # Récupération du montant => méthode du delta car pas toujours au même endroit sur la facture, et pas accessible via mot clé
    derniere_page = doc[-1]
    blocs_text = derniere_page.get_text("blocks")
        # On définit le delta de coordonnées qu'on a calculé avec un exemple
    delta = [155.03997802734375, 7.67999267578125, 135.83999633789062, 0.0]
        # On cherche d'abord la position du mot clé pour obtenir celle du montant
    mot_cle = 'Net à payer TTC'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if mot_cle in texte_bloc :
            bbox_0 = bloc[0:4] # On récupère les coordonnées de l'emplacement "Total TTC"
            bbox = [sum(x) for x in zip(bbox_0, delta)] # On définit la position avec celle du texte "Total TTC" + le delta
            break
        # On cherche le montant à partir de la position trouvée
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = derniere_page.get_text("text", clip=zone)
    montant = infos.split('\n')[-2].replace('EUR','').strip().replace('.',',')
    if top_avoir==1 : 
        montant = "-" + montant
        
    return [num_fact, date, montant]

# =============================================================================
# Grain de Sail => pas trouvé d'exemple avec avoir
# =============================================================================
def fonction_grain_de_sail(doc) :           
    # On ouvre la première page
    premiere_page = doc[0]   
    blocs_text = premiere_page.get_text('blocks')
    
    # Récupération du numéro de facture
    mot_cle_1 = 'Réf. :'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break 
    num_fact = infos.split(' ')[-1].strip()
   
    # Récupération de la date
    mot_cle_1 = 'Date facturation :'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break 
    date = infos.split(' ')[-1].strip()


    # Récupération du montant
    derniere_page = doc[-1]   
    blocs_text = derniere_page.get_text('blocks')
    mot_cle_1 = 'Total TTC'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break 
    montant = infos.split('\n')[-1].strip()

    return [num_fact, date, montant]

# =============================================================================
# TERRE ADELICE => pas d'exemple avec avoir
# =============================================================================
def fonction_terre_adelice(doc) :           
    # On ouvre la première page
    premiere_page = doc[0]   
    blocs_text = premiere_page.get_text('blocks')
    
    # Récupération du numéro de facture
    mot_cle_1 = 'N° FACTURE'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break 
    num_fact = infos.split('\n')[-1].strip()
   
    # Récupération de la date
    mot_cle_1 = 'DATE'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break 
    date = infos.split('\n')[-1].strip()
        # On transforme l'année en format aaaa
    date = date[0:-2] + '20' + date[-2:]

    # Récupération du montant
    derniere_page = doc[-1]   
    blocs_text = derniere_page.get_text('blocks')
    mot_cle_1 = 'NET A PAYER'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break 
    montant = infos.split('\n')[-1].strip()

    return [num_fact, date, montant]

# =============================================================================
# ENERGIE D'ICI => pas d'exemple avec avoir
# =============================================================================
def fonction_energie_ici(doc) :
    # On ouvre la première page
    premiere_page = doc[0]   
    blocs_text = premiere_page.get_text('blocks')

    # Récupération du numéro de facture et de la date
    mot_cle_1 = 'FACTURE N°'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break 
    date = infos.split(' ')[-1].strip()
    num_fact = infos.split(' ')[1].replace('N°','').strip()

    # Récupération du montant
    mot_cle_1 = 'Net à Payer'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break 
    montant = infos.split('\n')[-1].replace(' ','').replace('€','').strip()
    
    return [num_fact, date, montant]

# =============================================================================
# FERME BIO MARGERIE => pas d'exemple avec avoir
# =============================================================================
def fonction_margerie(doc) :
    # On ouvre la première page
    premiere_page = doc[0]   
    blocs_text = premiere_page.get_text('blocks')

    # Récupération du numéro de facture et de la date
    mot_cle_1 = 'Date'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break 
    date = infos.split('\n')[-1].strip()
    num_fact = infos.split('\n')[0].strip()

    # Récupération du montant
    derniere_page = doc[-1]   
    blocs_text = derniere_page.get_text('blocks')
    mot_cle_1 = 'TTC net à payer'
    for bloc in blocs_text:
        texte_bloc = bloc[4].strip()
        if (mot_cle_1 in texte_bloc) :
            infos = texte_bloc
            break 
    montant = infos.split('\n')[0].replace(' ','').replace('€','').strip()
    
    return [num_fact, date, montant]

# =============================================================================
# ALTERMONTS => pas d'exemple avoir avoir
# =============================================================================
def fonction_altermonts(doc) :
    # Ouverture de la 1er page
    premiere_page = doc[0]
    
    # Récupération du numéro de facture
    bbox = (32.189998626708984,294.6649169921875,86.8637466430664,305.47552490234375)
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = premiere_page.get_text("text", clip=zone)
    num_fact = infos.strip()
    
    # Récupération de la date
    bbox = (109.33000183105469,294.6649169921875,157.1182098388672,305.47552490234375)
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = premiere_page.get_text("text", clip=zone)
    date = infos.strip()
    
    # Récupération du montant 
    derniere_page = doc[-1]
    bbox = (527.2000122070312, 765.8829956054688, 568.0853881835938, 777.6170654296875)
    zone = fitz.Rect(bbox)
        # Récupérer le texte dans cette zone
    infos = derniere_page.get_text("text", clip=zone)
    montant = infos.replace('€','').strip()
        
    return [num_fact, date, montant]