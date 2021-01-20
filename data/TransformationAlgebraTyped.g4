	grammar TransformationAlgebraTyped;
	
	/*
    * This grammar can be used to parse typed strings of the Algebra of core concept transformation. Each string is a representation of a GIS workflow. It consists of a (left to right parsed) sequence of function or concept types. Function types can be be of different arity, and are supposed to be applied to the types to their right depending on their arity. Bracketed functions can become concepts, and thus inputs of functions, too. Further concepts are (unary, binary or ternary) relations and values. We use prefix notation: -: function prefix, * relation prefix.
	*
	* Example strings (tested with current version):
	*  
	*  	-: Nom -: Nom Nom Nom Nom			//function from Nom to some function from Nom to Nom (binary function), applied to two inputs
	* 	-: Ord -: O -: S * Nom O Ord O S	// ternary function that outputs a binary relation applied to three inputs
	*  	* O Nom * O					//relation ONomO (without any function application)
	* 	-: NomV * Nom S NomV		//function from NomV to relation NomS, applied to relation ONom
	*   -: Nom * Nom S Nom
	* 	-: (-: Nom NomV) * Nom S (-: Nom NomV) //This function type takes a function as input and outputs a binary relation
	*	-: Nom -: O * O Nom Nom O				
	* 	-: O -: O * O * Nom O -: Nom O Nom O 
	*/
	
     /*
     * Parser Rules
     */
	//Start rules: 
    	start : fa;				
	
	//Function Types		
		fb : IMPLIED WHITESPACE c ; //first input type of a function type
		fc1 :  fb WHITESPACE c ; 	//unary functions
		fc2 :	fb WHITESPACE fc1; 	//binary functions
		fc3	:	fb WHITESPACE fc2; 	//ternary functions	
		fc : fc1 | fc2 | fc3;
	
	//application rules for functions
		fa 		: 	fa0 | fa1 | fa2 | fa3;
		a1		: 	fa ; 				//applicant
		a2		:   fa WHITESPACE a1;	//applicant list of length 2
		a3		:   fa WHITESPACE a2;	//applicant list of length 3
		fa0		:	c ;		
		fa1		: 	fc1 WHITESPACE a1;
		fa2		:	fc2 WHITESPACE a2;
		fa3		: 	fc3 WHITESPACE a3;	
		
    	
	//Concept types (including type hierarchy):
		c 		:  v | r | rr | rrr | bfc;
		
		bfc : '(' fc ')' ; //bracketed function type (used as concept, i.e. as input to a function)
		
		v		: nomv | OV | LV | SV ;
		boolv 	: BOOLV ;
		nomv 	: NOMV | ordv | boolv ;
		ordv	: ORDV | itvv ;
		itvv	: ITVV | ratv ;
		ratv	: RATV | ev | iv | countv ;
		ev		: EV ;
		iv 		: IV ;
		countv	: COUNTV;
		
		r		: R | nom | nq ;
		nq		: NQ | O | L | S
		boolr 	: BOOL ;
		nom 	: NOM | ordr | boolr ;
		ordr	: ORD | itv ;
		itv		: ITV | rat ;		
		rat		: RAT | e | i | count ;
		e		: E ;
		i 		: I ;
		count	: COUNT;		
		
		rr		: REL WHITESPACE r WHITESPACE r ;
		
		rrr 	: REL WHITESPACE r WHITESPACE rr;
		
		
		
	//LEXER rules for type primitives	
	
		NOM		: 'Nom';
		ORD		: 'Ord';
		ITV		: 'Itv';
		RAT		: 'Ratio';
		COUNT	: 'Count' ;
		E		: 'Ext';
		I		: 'Int' ;
		O 		: 'O' ;
		L 		: 'L';
		S 		: 'S';
		BOOL	: 'Bool' ;
		R		: 'R' ;
		NQ		: 'NQ'
		
		NOMV	: 'NomV';
		ORDV	: 'OrdV';
		ITVV	: 'ItvV';
		RATV	: 'RatioV';
		COUNTV	: 'CountV' ;
		EV		: 'ExtV';
		IV		: 'IntV' ;
		OV 		: 'OV' ;
		LV 		: 'LV';
		SV 		: 'SV';
		BOOLV	: 'BoolV' ;
		
		REL 	: '*';	
		
		IMPLIED : '-:';
	
	
	//Basic lexer rules
		DATAV : [0-9]+ ;     
		WHITESPACE : ' ';	
		KEYWORD : ('a'..'z' | 'A'..'Z' | '-' | '_' | ':' | [0-9] )+ ; // used for naming data
		WS  : [ \t\r\n]+ -> skip ;	