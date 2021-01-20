	grammar TransformationAlgebra;
	
	/*
    * This grammar can be used to parse strings of the Algebra of core concept transformation. Each string is an abstract representation of a GIS workflow.
	*
	* Example string:
	* ratio fcont interpol pointmeasures temperature deify merge pi2 sigmae objectregions muni object Utrecht size pi1 interpol pointmeasures temperature deify merge pi2 sigmae objectregions muni object Utrecht
	* sigmae objectregions x object y
	*/
	
     /*
     * Parser Rules
     */
	//Start rules: 
    	start  : 	(r | rr | v );    
    	r 	:	(l | s | q | o);
    	rr 	:	(lq | sq | qs | oq | os);     
    	v	:	(ov | lv | sv| qv) ;
	
	
	
	//Value rules
	countv : COUNT o | GET  count | COUNTV ; 
	ratiov : FCONT lint | SIZE l  
		| RATIO ratiov WHITESPACE ratiov 
		| OCONT oratio | GET ratio| countv | RATIOV ;	
	intv : AVG lint | AVG oint | ratiov  |GET intt | INTV ;  
	ordv : MAX lord | MIN lord |  MAX oord  | MIN oord |  GET ordinal | intv | ORDV;  	
	nomv : ordv | GET nom | TOPOV | NOMV;
	qv : GET  q | nomv | ordv | intv | ratiov | countv;
	sv : REIFY l | GET  s | MERGE s | SV;
	lv : GET l ;		
	ov : GET  o | DATAOBJV ;
	
	
	
	// R rules	
	l : DEIFY sv | PI1  lint  | PI1  lord  | PI1  lnom | PI1  lq | PI1 lratio |  PI1 linto | PI1 lnomo ;	//First apply the most specific function
	s : PI1  sint  | PI1  sord  | PI1  snom | PI1  lq | PI2 os ;	//First apply the most specific function
	o : PI1  os  | PI1  oratio  |  PI1  oint  |  PI1  oord  | PI1  onom| PI1  oq | PI1 onomo | PI2 onomo | PI3 lnomo | PI3 onomo;
	count : PI2 ocount ;   
	ratio : PI2 oratio | PI2 lratio | count;
	intt : PI1 ints | PI2 oint |  PI2 lint |ratio ;	
	ordinal : PI1  ords | intt ;
	nom : PI1 noms | ordinal ;
	q : PI1  qs | nom ;
	
	// RR rules		
	lratio : DATAFIELD ;		
	lint : INTERPOL sint WHITESPACE l | SIGMASE lint WHITESPACE intv|  BOWTIE lint WHITESPACE l   | GROUPBYAVG lintl | lratio   ;
	lord : REVERT ords | SIGMASE lord WHITESPACE ordv |  BOWTIE lord WHITESPACE l   | groupbyaggord lordl | lint ;
	lnom : REVERT snom | SIGMAE lnom WHITESPACE nomv  | lord; 
	lq : SIGMAE lq WHITESPACE qv | BOWTIE lq WHITESPACE l  |lnom;		
	
	ords : INVERT lord | SIGMASE ords WHITESPACE ordv | DATACONTOUR ;
	ints : DATACONTOURLINE ; 
	noms : SIGMAE noms WHITESPACE nomv | ords ; 
	qs : noms ;	
	
	sint : DATAPM ;		
	sord : sint ;	
	snom : DATAAMOUNT | INVERT lnom | SIGMAE snom WHITESPACE nomv | sord ;
	sq : snom ;
	
	os : SIGMAE os WHITESPACE ov | BOWTIE os WHITESPACE o | DATAOBJS ;	
	ocount : SIGMAE ocount WHITESPACE ov | BOWTIE ocount WHITESPACE o | GROUPBYCOUNT onomo | GROUPBYAVG ocounto | GROUPBYSUM ocounto | DATAOBJCOUNT ;			
	oratio :BOWTIE oratio WHITESPACE o | BOWTIERATIO oratio WHITESPACE oratio | GROUPBYAVG oratioo | GROUPBYSUM oratioo | GROUPBYAVG lratioo | GROUPBYSIZE lnomo | DATAOBJQ | ocount ; 
	oint : SIGMASE oint WHITESPACE intv|  BOWTIE oint WHITESPACE o  | GROUPBYAVG ointo | GROUPBYAVG linto | oratio	;
	oord : SIGMASE oord WHITESPACE ordv |  BOWTIE oord WHITESPACE o  | groupbyaggord oordo |  oint ;
	onom : SIGMAE onom WHITESPACE nomv | oord ;
	oq : SIGMAE oq WHITESPACE qv |  BOWTIE oq WHITESPACE o  | onom;
	
	
	
	//RRR rules
	ocounto : BOWTIESTAR onomo WHITESPACE ocount ;
	oratioo : ODIST os WHITESPACE os  |NDIST o WHITESPACE o WHITESPACE oratioo | BOWTIESTAR onomo WHITESPACE oratio ;		
	ointo : BOWTIESTAR onomo WHITESPACE oint  | oratioo ;	
	oordo :  SIGMASE oordo WHITESPACE ordv  |  ointo  ;
	onomo : OTOPO os WHITESPACE os  | SIGMAE onomo WHITESPACE nomv   |  oordo 	;
	
	lratioo : LODIST l WHITESPACE o | BOWTIESTAR lnomo WHITESPACE lratio ;
	linto : BOWTIESTAR lnomo WHITESPACE lint | lratioo ;	
	lnomo : LOTOPO l WHITESPACE  os | SIGMAE lnomo WHITESPACE nomv  ;
	
	lratiol : LDIST l WHITESPACE l | BOWTIESTAR lnoml WHITESPACE lratio;
	lintl : BOWTIESTAR lnoml WHITESPACE lint  | lratiol ;
	lordl :  SIGMASE lordl WHITESPACE ordv  | lintl ; 	
	lnoml :  SIGMAE lnoml WHITESPACE nomv |lbooll |lordl; 	
	lbooll : LVIS l WHITESPACE l WHITESPACE oint  | SIGMAE lbooll WHITESPACE BOOLV ; 	
	
		
	//Group by superfunction		
	groupbyaggord : GROUPBYMIN |	GROUPBYMAX;
	
	/*
     	* Lexer Rules
     */
	//Functions:
	
 	//Value Derivations
	RATIO : 'ratio '  ;
	
	// Statistical operations
	AVG : 'avg ' ; 
	MIN : 'min ' ;
	MAX : 'max ' ;
	
	// Aggregations of collections
	COUNT : 'count ';
	SIZE : 'size ';
	MERGE : 'merge ';
	
	//Conversions
	REIFY : 'reify ' ;
	DEIFY : 'deify ';
	GET : 'get ' ;
	INVERT: 'invert ';
	REVERT: 'revert ';
	
	//Amount operations
	FCONT :  'fcont ' ;
	OCONT :  'ocont ' ;
	
	//Relational operations
	PI1 : 'pi1 ' ; //project 1
	PI2 : 'pi2 ' ; //project 2
	PI3	: 'pi3 ' ; //project 3
	SIGMAE : 'sigmae '  ; //Select  =
	SIGMASE : 'sigmale '  ; //Select <=
	BOWTIE : 'bowtie ' ; //Subset relation
	BOWTIESTAR : 'bowtie* '; //Join quality with quantifed relation
	BOWTIERATIO : 'bowtie_ratio ';	//Join two qualities
	GROUPBYAVG : 'groupby_avg ' ; //Group by
	GROUPBYSUM : 'groupby_sum ' ;
	GROUPBYMIN : 'groupby_min ' ;
	GROUPBYMAX : 'groupby_max ' ;
	GROUPBYSIZE : 'groupby_size ' ;
	GROUPBYCOUNT : 'groupby_count ' ;
	
	//Geometric transformations
	INTERPOL : 'interpol ' ;
	ODIST : 'odist ' ;
	LDIST : 'ldist ';
	LODIST : 'lodist ' ;
	OTOPO : 'otopo ' ;
	LOTOPO : 'lotopo ' ;
	NDIST : 'ndist ' ;
	LVIS : 'lvis ' ;
	
	//Data inputs:
	DATAPM : 'pointmeasures ' KEYWORD ;
	DATAAMOUNT  :  'amountpatches ' KEYWORD ;
  	DATACONTOUR :  'contour '  KEYWORD  ;
	DATAOBJQ :  'objects ' KEYWORD  ;
	DATAOBJS :  'objectregions ' KEYWORD;
	DATAOBJV : 'object ' KEYWORD ;
	DATACONTOURLINE :  'contourline ' KEYWORD  ;
	DATAOBJCOUNT :  'objectcounts ' KEYWORD  ;
	DATAFIELD :  'field ' KEYWORD ;	
	TOPOV : 'in' ;
	SV : 'region ' DATAV ; 
	COUNTV : 'count ' DATAV ;
	RATIOV : 'ratio ' DATAV ;
	INTV : 'interval ' DATAV ;
	ORDV : 'ordinal ' DATAV | 'ordinal ' KEYWORD ;	
	BOOLV : 'true' | 'false';
	NOMV : 'nominal ' KEYWORD ;
	
	
	
	//Basic lexer rules
	DATAV : [0-9]+ ;     
    WHITESPACE : ' ';	
	KEYWORD : ('a'..'z' | 'A'..'Z' | '-' | '_' | ':' | [0-9] )+ ; // used for naming data
	WS  : [ \t\r\n]+ -> skip ;	